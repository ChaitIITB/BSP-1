"""GenRec-style LoRA fine-tune for ranking researchers. Runs on a Kaggle GPU notebook (T4); nothing here is meant for the local GPU.
Data: a Kaggle dataset holding train.jsonl / val.jsonl / test.jsonl (built by build_genrec_data.py).
Env knobs: MODEL (default Qwen/Qwen2.5-1.5B), EPOCHS (3), MAX_STEPS (-1 = full; use ~40 for a smoke test), BASE_EVAL_N (100), TEST_N (all)."""
import os
os.environ.setdefault('CUDA_VISIBLE_DEVICES', '0')      # one GPU: avoids DataParallel quirks with LoRA
import glob, json, time, random, itertools
import numpy as np, torch, transformers
from scipy.stats import kendalltau
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL = os.environ.get('MODEL', 'Qwen/Qwen2.5-1.5B')
EPOCHS = float(os.environ.get('EPOCHS', 3)); MAX_STEPS = int(os.environ.get('MAX_STEPS', -1))
BASE_EVAL_N = int(os.environ.get('BASE_EVAL_N', 100)); TEST_N = int(os.environ.get('TEST_N', 100000))
CUTOFF, LR, BATCH, MICRO = 512, 3e-4, 32, 8             # GenRec: lr 3e-4, batch 128, cutoff 256; we use batch 32 (only 5k examples) and cutoff 512
LORA_R, LORA_ALPHA, LORA_DROPOUT, TARGETS = 8, 16, 0.05, ['q_proj', 'v_proj']   # same LoRA recipe as GenRec's rec.py
OUT = '/kaggle/working' if os.path.isdir('/kaggle/working') else './out'
DATA = os.path.dirname(next(iter(glob.glob('/kaggle/input/**/train.jsonl', recursive=True)), './data/train.jsonl'))
print('data dir', DATA, '| model', MODEL, '| gpu', torch.cuda.get_device_name(0) if torch.cuda.is_available() else None)
rd = lambda s: [json.loads(l) for l in open(f'{DATA}/{s}.jsonl', encoding='utf-8')]
train, val, test = rd('train'), rd('val'), rd('test')[:TEST_N]

tok = AutoTokenizer.from_pretrained(MODEL)
if tok.pad_token is None: tok.pad_token = tok.eos_token

def prompt(r):
    return f"{r['instruction']}\n\n### Input:\n{r['input']}\n\n### Response:\n"

def encode(r):
    p = tok(prompt(r))['input_ids']; o = tok(r['output'])['input_ids'] + [tok.eos_token_id]
    ids = (p + o)[:CUTOFF]; lab = ([-100] * len(p) + o)[:CUTOFF]       # loss on the answer only
    return dict(input_ids=ids, attention_mask=[1] * len(ids), labels=lab)

try:
    model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.float16).cuda()
except TypeError:
    model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float16).cuda()

# ---------------- evaluation ----------------
def parse(text, cands):
    seen = []
    for n in [x.strip() for x in text.split('>')]:
        if n in cands and n not in seen: seen.append(n)
    valid = len(seen) == len(cands) and len(text.split('>')) == len(cands)
    return seen + [c for c in cands if c not in seen], valid                # complete a partial answer in input order

@torch.no_grad()
def generate(m, rows, bs=16):
    tok.padding_side = 'left'; m.eval(); outs = []
    for i in range(0, len(rows), bs):
        b = [prompt(r) for r in rows[i:i + bs]]
        x = tok(b, return_tensors='pt', padding=True).to('cuda')
        y = m.generate(**x, max_new_tokens=96, do_sample=False, num_beams=1, pad_token_id=tok.pad_token_id)
        outs += tok.batch_decode(y[:, x['input_ids'].shape[1]:], skip_special_tokens=True)
    return outs

def metrics(rows, outs):
    taus, top1, valid, ndcg = [], [], [], []
    for r, o in zip(rows, outs):
        pred, ok = parse(o, r['cands']); gold = r['gold']; valid.append(ok)
        g = {n: len(gold) - i for i, n in enumerate(gold)}                  # gold relevance: best = K
        taus.append(kendalltau([g[n] for n in pred], list(range(len(pred), 0, -1)))[0])
        top1.append(pred[0] == gold[0])
        dcg = sum(g[n] / np.log2(i + 2) for i, n in enumerate(pred)); idcg = sum(g[n] / np.log2(i + 2) for i, n in enumerate(gold))
        ndcg.append(dcg / idcg)
    return dict(n=len(rows), valid_format=float(np.mean(valid)), top1=float(np.mean(top1)), kendall_tau=float(np.nanmean(taus)), ndcg=float(np.mean(ndcg)))

def heuristic(rows):   # text-only baseline: more papers = higher (parsed from the profile line)
    import re
    outs = []
    for r in rows:
        k = {}
        for line in r['input'].split('\n'):
            m = re.match(r'(.*) \((\d+) papers', line); k[m.group(1)] = int(m.group(2))
        outs.append(' > '.join(sorted(r['cands'], key=lambda n: -k[n])))
    return outs

res = {'model': MODEL, 'train_examples': len(train), 'test_examples': len(test)}
rng = random.Random(0)
res['random_expected'] = dict(top1=1 / 6, kendall_tau=0.0)
res['baseline_paper_count'] = metrics(test, heuristic(test))
print('paper-count baseline', res['baseline_paper_count'])
if BASE_EVAL_N > 0:
    sub = test[:BASE_EVAL_N]; t0 = time.time()
    res['base_model_zero_shot'] = metrics(sub, generate(model, sub)); print('zero-shot', res['base_model_zero_shot'], round(time.time() - t0), 's')

# ---------------- training ----------------
model.gradient_checkpointing_enable(); model.enable_input_require_grads(); model.config.use_cache = False
model = get_peft_model(model, LoraConfig(r=LORA_R, lora_alpha=LORA_ALPHA, target_modules=TARGETS, lora_dropout=LORA_DROPOUT, bias='none', task_type='CAUSAL_LM'))
model.print_trainable_parameters()
ds = [encode(r) for r in train]
args = transformers.TrainingArguments(
    output_dir=f'{OUT}/ckpt', per_device_train_batch_size=MICRO, gradient_accumulation_steps=BATCH // MICRO, warmup_steps=10,
    num_train_epochs=EPOCHS, max_steps=MAX_STEPS, learning_rate=LR, fp16=True, logging_steps=5, optim='adamw_torch',
    save_strategy='steps', save_steps=20, save_total_limit=2, report_to='none', lr_scheduler_type='cosine')
trainer = transformers.Trainer(model=model, train_dataset=ds, args=args,
                               data_collator=transformers.DataCollatorForSeq2Seq(tok, pad_to_multiple_of=8, return_tensors='pt', padding=True))
t0 = time.time()
ck = max(glob.glob(f'{OUT}/ckpt/checkpoint-*'), key=os.path.getmtime, default=None)   # resume if the session restarted
trainer.train(resume_from_checkpoint=ck)
dt = time.time() - t0; ntok = sum(len(d['input_ids']) for d in ds) * (EPOCHS if MAX_STEPS < 0 else min(EPOCHS, MAX_STEPS * BATCH / len(ds)))
res['train_seconds'] = dt; res['approx_tokens_per_sec'] = ntok / dt
print('train seconds', round(dt), 'approx tokens/s', round(ntok / dt))
model.save_pretrained(f'{OUT}/lora_adapter')

# ---------------- test ----------------
outs = generate(model, test)
res['fine_tuned'] = metrics(test, outs); print('fine-tuned', res['fine_tuned'])
json.dump(res, open(f'{OUT}/results.json', 'w'), indent=1)
json.dump([dict(cands=r['cands'], gold=r['gold'], pred=o) for r, o in zip(test[:100], outs[:100])], open(f'{OUT}/sample_predictions.json', 'w'), indent=1, ensure_ascii=False)
