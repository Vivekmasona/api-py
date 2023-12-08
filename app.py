from pytube import YouTube
from flask import Flask, session, url_for, send_file, render_template, redirect, request
from io import BytesIO

app = Flask(__name__)
app.config["SECRET_KEY"] = "my_secret_key"

@app.route("/", methods=["POST", "GET"])
def index():
    if request.method == "POST":
        session["link"] = request.form.get("url")
        url = YouTube(session["link"])
        url.check_availability()
        return render_template("download.html", url=url)

    return render_template('index.html')

@app.route("/audio/<video_id>", methods=["GET"])
def audio(video_id):
    youtube_link = f"https://www.youtube.com/watch?v={video_id}"
    buffer = BytesIO()
    url = YouTube(youtube_link)
    audio_stream = url.streams.filter(only_audio=True).first()

    if audio_stream:
        audio_stream.stream_to_buffer(buffer)
        buffer.seek(0)

        return send_file(buffer, as_attachment=True, download_name=f"{url.title}.mp3", mimetype="audio/mpeg")

    return "Invalid or missing YouTube link parameter."

@app.route("/video", methods=["GET"])
def download():
    youtube_link = request.args.get("url")
    if youtube_link:
        buffer = BytesIO()
        url = YouTube(youtube_link)
        video = url.streams.get_highest_resolution()

        # Stream the video to the buffer
        video.stream_to_buffer(buffer)
        buffer.seek(0)

        return send_file(buffer, as_attachment=True, download_name=video.title, mimetype=video.mime_type)

    return "Invalid or missing YouTube link parameter."

if __name__ == '__main__':
    app.run(debug=True)


