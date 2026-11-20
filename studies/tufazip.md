# TufaZip v2 — online Transformer для lossless-сжатия enwik9

[Структурированная запись и связи](../catalog/studies/tufazip.md)

**Тип:** авторское инженерное исследование + открытый код (MIT), не научная публикация с подтверждённым peer review. Автор — Tommy He, Tufa Labs.

**Первоисточники:** [полный авторский технический разбор (14.10.2026)](https://tufalabs.ai/research/tufazip/), [репозиторий @b9d678d](https://github.com/Tufalabs/tufazip/tree/b9d678db3a0f726e117c8cab51927975830395ac), [результат в официальном Large Text Compression Benchmark](https://mattmahoney.net/dc/text.html), [MIT LICENSE](https://github.com/Tufalabs/tufazip/blob/b9d678db3a0f726e117c8cab51927975830395ac/LICENSE). Код зафиксирован 21.11.2026. В статье описаны v1 (online random init) и v2 (offline C2 prior + online). Не следует смешивать их результаты, время и расход памяти.

**Маршрут:** **Рассмотрен и отложен** — `DEFERRED / NO_FIT / NEEDS_PROJECT_SPECIFIC_WORKLOAD`. Полный первичный текст и код изучены; ни один из 45 текущих проектов не имеет обоснованной потребности в недельном GPU lossless compression с exact deterministic decoder. Backlinks в project-registry не создаются.

**AUTHOR_REPORTED:** 1 000 000 000 байт enwik9 → **105 388 353 байта общего размера v2** (100 958 324 payload + 4 430 029 decoder ZIP с переносимыми приоритетными весами). Transformer 12 слоёв / 163 млн параметров, компактный offline Cycle2 prior в исходной 34M-модели, 4.33 MB квантованных весов. Online-only v1 105 979 069 байт. Нейросеть — единственный **предиктор**, но в конвейере также есть обратимое препроцессирование и арифметическое кодирование.

**Ограничения:** `tufazip` из текущего upstream — прежде всего декодер фиксированного артефакта enwik9, не опубликованный универсальный drop-in архиватор. Строгие проверки **двух NVIDIA B200**, CUDA 13.0, cuDNN 9.20, Python 3.12.3, PyTorch 2.12.0+cu130; авторские времена 631 548 сек. encode (без offline pretraining) / 645 748 сек. decode; time of offline training не включён. Снижение размера не говорит об улучшении retrieval, DBA ответов или agent memory.

**INDEPENDENTLY_VERIFIED (ограниченно):** просмотрены весь авторский HTML, tracked source `nn.py`, `tufazip`, `arithmetic_coder.py`, `checkpoint_utils.py`, `preprocess.c` и `README.md`; локальные SHA-256 `weights.bin` и `enwik9.voc` совпали с указанными в decoder. Исходный decode/encode на B200 **NOT_RUN**, полный enwik9 round-trip и точность leaderboard независимо **NOT_REPRODUCED**.

[Подробный source review и матрица](../reviews/tufazip/2026-11-21.md) · [сводка периода](../portfolio/2026-11-21/review.md).
