# OpenRouter AI Interface

## Giới thiệu

OpenRouter AI Interface là một ứng dụng web đơn giản cho phép người dùng tương tác với các mô hình AI thông qua OpenRouter API. Ứng dụng này được xây dựng bằng Python (Flask) và có thể dễ dàng triển khai trên Vercel.

## Tính năng

- Giao diện người dùng đơn giản và trực quan
- Hỗ trợ nhiều mô hình AI miễn phí từ OpenRouter:
  - DeepSeek R1
  - Qwen 2.5 VL 72B
  - DeepSeek Chat
  - Google Gemini 2.0 Flash
  - Google Gemini 2.0 Pro
  - Google Gemini 2.0 Flash Thinking
  - Meta Llama 3.3 70B
- Xử lý lỗi và hiển thị thông báo phù hợp
- Thiết kế responsive, hoạt động tốt trên cả máy tính và thiết bị di động

## Cài đặt và Chạy Locally

### Yêu cầu

- Python 3.9 hoặc cao hơn
- Tài khoản OpenRouter và API key

### Các bước cài đặt

1. Clone repository này:

2. Cài đặt các thư viện cần thiết:
pip install -r requirements.txt

3. Tạo file `.env` và thêm API key của OpenRouter:
OPENROUTER_API_KEY=your_api_key_here

4. Chạy ứng dụng:
python app.py

5. Mở trình duyệt và truy cập `http://127.0.0.1:5000`

## Triển khai lên Vercel

### Sử dụng Git (Khuyến nghị)

1. Push code lên repository Git (GitHub, GitLab, hoặc Bitbucket)
2. Đăng nhập vào tài khoản Vercel
3. Nhấp vào "New Project"
4. Import repository của bạn
5. Cấu hình project (đảm bảo phiên bản Python được đặt là 3.12)
6. Nhấp vào "Deploy"

### Sử dụng Vercel CLI

1. Cài đặt Vercel CLI:
npm install -g vercel

2. Di chuyển đến thư mục project và chạy:
vercel

3. Làm theo hướng dẫn để triển khai project

### Cấu hình biến môi trường trên Vercel

1. Vào dashboard Vercel
2. Chọn project của bạn sau khi triển khai
3. Vào "Settings" > "Environment Variables"
4. Thêm biến mới:
- Name: `OPENROUTER_API_KEY`
- Value: API key của OpenRouter
5. Lưu thay đổi

## Cách sử dụng

1. Chọn mô hình AI từ dropdown menu
2. Nhập prompt vào ô văn bản
3. Nhấp vào nút "Generate Response"
4. Đợi kết quả được hiển thị

## Cấu trúc project
openrouter-ai-interface/
├── api/
│   ├── index.py       # Xử lý route chính
│   └── generate.py    # Xử lý API call đến OpenRouter
├── index.html         # Giao diện người dùng
├── requirements.txt   # Các thư viện cần thiết
└── vercel.json        # Cấu hình triển khai Vercel

## Giới hạn và lưu ý

- Runtime Python của Vercel đang ở giai đoạn Beta
- Cold starts có thể ảnh hưởng đến thời gian phản hồi
- Gói miễn phí có giới hạn về thời gian thực thi và kích thước function
- Đảm bảo các dependencies được chỉ định đúng trong `requirements.txt`

## Công nghệ sử dụng

- Python Flask: Backend framework
- HTML/CSS/JavaScript: Frontend
- Vercel: Hosting và triển khai
- OpenRouter API: Cung cấp truy cập đến các mô hình AI

## Đóng góp

Mọi đóng góp đều được hoan nghênh! Vui lòng tạo issue hoặc pull request nếu bạn muốn cải thiện project.

## Giấy phép

[MIT License](LICENSE)