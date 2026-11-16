"""Cut a person out of a video: writes a lossless grayscale matte (white = person, black = background) that
tools/shorts.py uses to put graphics BEHIND the presenter.

  python tools/matte.py projects/<name>/presenter.mp4                  # -> projects/<name>/presenter-matte.mkv
  python tools/matte.py clip.mp4 --out matte.mkv --width 720 --ratio 0.375 [--seconds 5]

Model: Robust Video Matting (mobilenetv3, ONNX) in tools/models/, run on CPU with onnxruntime. Runs locally; nothing is uploaded.
--width is the size the model sees (bigger = finer hair/edges, slower); --ratio is RVM's downsample_ratio.
"""
import argparse, os, pathlib, subprocess, sys, time
import cv2, numpy as np, onnxruntime as ort

MODEL = pathlib.Path(__file__).resolve().parent / "models" / "rvm_mobilenetv3_fp32.onnx"


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,r_frame_rate:format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout.split()
    w, h, fps = out[0].split(",")[:3]
    n, d = fps.split("/")
    return int(w), int(h), float(n) / float(d), float(out[1] if len(out) > 1 else 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--out")
    ap.add_argument("--width", type=int, default=720)
    ap.add_argument("--ratio", type=float, default=0.375)
    ap.add_argument("--seconds", type=float, help="only the first N seconds (for a quick test)")
    a = ap.parse_args()
    src = pathlib.Path(a.video).resolve()
    out = pathlib.Path(a.out) if a.out else src.with_name(src.stem + "-matte.mkv")
    if not MODEL.exists():
        sys.exit(f"model missing: {MODEL}")
    W, H, fps, dur = probe(src)
    iw = a.width - a.width % 2
    ih = int(round(iw * H / W / 2) * 2)
    total = int(round((a.seconds or dur) * fps))

    opts = ort.SessionOptions()
    opts.intra_op_num_threads = os.cpu_count() or 4
    sess = ort.InferenceSession(str(MODEL), sess_options=opts, providers=["CPUExecutionProvider"])
    rec = [np.zeros((1, 1, 1, 1), np.float32) for _ in range(4)]
    ratio = np.array([a.ratio], np.float32)

    dec_cmd = ["ffmpeg", "-loglevel", "error", "-i", str(src)] + (["-t", str(a.seconds)] if a.seconds else []) + \
              ["-vf", f"scale={iw}:{ih}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    enc_cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{W}x{H}",
               "-r", f"{fps:.5f}", "-i", "-", "-c:v", "ffv1", "-pix_fmt", "gray", str(out)]
    dec = subprocess.Popen(dec_cmd, stdout=subprocess.PIPE)
    enc = subprocess.Popen(enc_cmd, stdin=subprocess.PIPE)
    t0, n = time.time(), 0
    size = iw * ih * 3
    while True:
        buf = dec.stdout.read(size)
        if len(buf) < size:
            break
        x = np.frombuffer(buf, np.uint8).reshape(ih, iw, 3).astype(np.float32) / 255.0
        x = np.ascontiguousarray(x.transpose(2, 0, 1)[None])
        fgr, pha, *rec = sess.run(None, {"src": x, "r1i": rec[0], "r2i": rec[1], "r3i": rec[2], "r4i": rec[3],
                                         "downsample_ratio": ratio})
        alpha = (pha[0, 0] * 255).clip(0, 255).astype(np.uint8)
        alpha = cv2.resize(alpha, (W, H), interpolation=cv2.INTER_CUBIC)
        alpha = cv2.GaussianBlur(alpha, (5, 5), 0)  # soften the edge a touch so it blends instead of looking cut out
        enc.stdin.write(alpha.tobytes())
        n += 1
        if n % 60 == 0:
            rate = n / (time.time() - t0)
            print(f"frame {n}/{total}  {rate:.1f} fps  ~{(total - n) / rate / 60:.1f} min left", flush=True)
    enc.stdin.close()
    enc.wait()
    dec.wait()
    print(f"wrote {out} ({n} frames, {time.time() - t0:.0f}s)")


main()
