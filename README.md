# learn-in-one-night

Claude Code skill tạo **tài liệu ôn thi gọn** cho bất kỳ môn nào: thuật ngữ giữ ngôn ngữ của đề, giải thích tiếng Việt 1 dòng, cụm từ đề hay dùng, bẫy đề, công thức, và chế độ tự kiểm tra.

## Cách hoạt động

1. Hỏi bằng popup: môn học, ngôn ngữ đề, hình thức thi, thời gian còn lại, nguồn tài liệu (slide, đề cũ, Quizlet…), độ gọn.
2. Trích nội dung từ `.pptx`, `.ppt`, `.pdf`, `.docx`, `.xlsx`, `.svg`, `.txt/.md/.html/.csv` (`scripts/extract_sources.py`).
3. Rút ra các dạng câu hỏi và bẫy từ đề cũ.
4. Viết một file HTML theo từng chương từ `assets/template.html`, rồi kiểm tra bằng `scripts/check_html.py`.

## Cài đặt

```bash
git clone https://github.com/thanhsu263/learn-in-one-night ~/.claude/skills/learn-in-one-night
pip install olefile pymupdf openpyxl
```

Thư viện Python chỉ cần cho định dạng tương ứng: `olefile` cho `.ppt`, `pymupdf` (hoặc `pypdf`) cho `.pdf`, `openpyxl` cho `.xlsx`. File `.pptx`/`.docx` không cần cài thêm gì.

## Dùng

Trong Claude Code, gõ `/learn-in-one-night` (hoặc kèm mã môn: `/learn-in-one-night MLN111`), hay nói tự nhiên như "ôn thi môn X giúp mình".

## Cấu trúc

```
SKILL.md                    hướng dẫn quy trình cho Claude
assets/template.html        khung HTML (ô Nhớ, bảng thuật ngữ, Bẫy đề, quiz mode)
assets/example-swt301.html  ví dụ hoàn chỉnh (SWT301 – Software Testing)
references/domains.md       gợi ý thành phần chính theo từng lĩnh vực
scripts/extract_sources.py  trích văn bản từ slide/tài liệu
scripts/check_html.py       kiểm tra file HTML kết quả
```
