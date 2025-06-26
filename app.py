import subprocess
import os
from flask import Flask, request, send_file, render_template
from pathlib import Path
import zipfile

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        shortcode = url.strip().split('/')[-2]

        base_dir = Path(__file__).parent
        temp_dir = base_dir / f"temp_{shortcode}"
        temp_dir.mkdir(exist_ok=True)

        output_template = str(temp_dir / f"{shortcode}.%(ext)s")

        # yt-dlp 다운로드
        try:
            result = subprocess.run([
                "yt-dlp", url,
                "-o", output_template
            ], check=True)
        except subprocess.CalledProcessError as e:
            return f"❌ yt-dlp 실행 오류: {e}"

        # 압축
        zip_path = base_dir / f"{shortcode}.zip"
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for f in temp_dir.iterdir():
                zipf.write(f, arcname=f.name)

        # 파일 정리
        for f in temp_dir.iterdir():
            f.unlink()
        temp_dir.rmdir()

        return send_file(zip_path, as_attachment=True)

    return render_template('index.html')


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
