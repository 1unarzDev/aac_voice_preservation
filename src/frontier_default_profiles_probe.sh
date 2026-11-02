#!/usr/bin/env bash
# one model at a time under the blocking GPU lock
cd ~/aac-voice-preservation
for k in "$@"; do
  declare -A P=([qwen]=8091 [llama]=8092 [gemma]=8093 [qwen14]=8094 [nemo]=8095)
  declare -A A=([qwen]=qwen2.5-7b [llama]=llama3.1-8b [gemma]=gemma3-4b [qwen14]=qwen2.5-14b [nemo]=mistral-nemo-12b)
  flock /tmp/aacv_gpu.lock bash -c "
    PARALLEL=4 CTX_PER_SLOT=1024 src/serve_local.sh $k && . .venv/bin/activate && python src/frontier_default_profiles_probe.py --model ${A[$k]} --port ${P[$k]} --workers 4 $LIMIT
    docker rm -f aacv-$k >/dev/null 2>&1"
done
echo ALLDONE
