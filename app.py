from flask import Flask, request, render_template, send_file
import instaloader
import requests
from pathlib import Path
import zipfile
import os

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        shortcode = url.strip().split('/')[-2]
        L = instaloader.Instaloader()
        post = instaloader.Post.from_shortcode(L.context, shortcode)

        base_dir = Path(__file__).parent
        temp_dir = base_dir / f"temp_{shortcode}"
        temp_dir.mkdir(exist_ok=True)

        files = []

        if post.typename == "GraphSidecar":
            for i, node in enumerate(post.get_sidecar_nodes()):
                ext = "mp4" if node.is_video else "jpg"
                url = node.video_url if node.is_video else node.display_url
                filename = temp_dir / f"{shortcode}_{i+1}.{ext}"
                r = requests.get(url)
                if r.status_code == 200:
                    with open(filename, 'wb') as f:
                        f.write(r.content)
                    files.append(filename)
        else:
            # 단일 이미지 또는 영상
            ext = "mp4" if post.is_video else "jpg"
            url = post.video_url if post.is_video else post.url
            filename = temp_dir / f"{shortcode}.{ext}"
            r = requests.get(url)
            if r.status_code == 200:
                with open(filename, 'wb') as f:
                    f.write(r.content)
                files.append(filename)

        # zip 압축
        zip_path = base_dir / f"{shortcode}.zip"
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for f in files:
                zipf.write(f, arcname=f.name)

        # 파일 정리 (슬라이드 항목 개별 파일 삭제)
        for f in files:
            f.unlink()
        temp_dir.rmdir()

        return send_file(zip_path, as_attachment=True)

    return render_template('index.html')


# ✅ 이 아래 부분이 중요!
if __name__ == '__main__':
    app.run(debug=True)
