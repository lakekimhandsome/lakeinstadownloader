from flask import Flask, request, render_template, send_file
import instaloader
import requests
from pathlib import Path
import zipfile
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        shortcode = url.strip().split('/')[-2]

        # Instaloader 초기화 및 로그인
        L = instaloader.Instaloader()
        username = os.getenv('INSTAGRAM_USERNAME')
        password = os.getenv('INSTAGRAM_PASSWORD')

        try:
            L.login(username, password)
        except instaloader.exceptions.BadCredentialsException:
            return "❌ 인스타그램 로그인 실패. 계정 정보를 확인하세요."
        except Exception as e:
            return f"❌ 로그인 중 오류 발생: {str(e)}"

        try:
            post = instaloader.Post.from_shortcode(L.context, shortcode)
        except Exception as e:
            return f"❌ 게시물 정보 불러오기 실패: {str(e)}"

        base_dir = Path(__file__).parent
        temp_dir = base_dir / f"temp_{shortcode}"
        temp_dir.mkdir(exist_ok=True)

        files = []

        try:
            # 슬라이드형 게시물
            if post.typename == "GraphSidecar":
                for i, node in enumerate(post.get_sidecar_nodes()):
                    ext = "mp4" if node.is_video else "jpg"
                    media_url = node.video_url if node.is_video else node.display_url
                    filename = temp_dir / f"{shortcode}_{i+1}.{ext}"
                    r = requests.get(media_url)
                    if r.status_code == 200:
                        with open(filename, 'wb') as f:
                            f.write(r.content)
                        files.append(filename)
            else:
                # 단일 이미지 or 영상
                ext = "mp4" if post.is_video else "jpg"
                media_url = post.video_url if post.is_video else post.url
                filename = temp_dir / f"{shortcode}.{ext}"
                r = requests.get(media_url)
                if r.status_code == 200:
                    with open(filename, 'wb') as f:
                        f.write(r.content)
                    files.append(filename)
        except Exception as e:
            return f"❌ 미디어 다운로드 중 오류 발생: {str(e)}"

        # zip 압축
        zip_path = base_dir / f"{shortcode}.zip"
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for f in files:
                zipf.write(f, arcname=f.name)

        # 정리
        for f in files:
            f.unlink()
        temp_dir.rmdir()

        return send_file(zip_path, as_attachment=True)

    return render_template('index.html')


# ✅ Render 배포용 실행
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
