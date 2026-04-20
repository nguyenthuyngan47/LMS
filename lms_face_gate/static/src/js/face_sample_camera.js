/** @odoo-module **/

import { onMounted } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";

patch(FormController.prototype, {
    setup() {
        super.setup(...arguments);
        onMounted(() => this._initFaceCamera());
    },

    _initFaceCamera() {
        const mount = document.getElementById("face-camera-mount");
        if (!mount || mount.dataset.bound === "1") return;
        mount.dataset.bound = "1";

        const video = document.getElementById("face-video");
        const canvas = document.getElementById("face-canvas");
        const preview = document.getElementById("face-preview");
        const previewWrap = document.getElementById("face-preview-wrap");
        const btnOpen = document.getElementById("btn-open-face-camera");
        const btnCapture = document.getElementById("btn-capture-face");
        const btnRetake = document.getElementById("btn-retake-face");
        const btnSave = document.getElementById("btn-save-face");
        const btnGroup = document.getElementById("face-btn-group");
        const msgEl = document.getElementById("face-msg");

        if (!btnOpen || !video || !canvas || !preview || !previewWrap || !btnCapture || !btnRetake || !btnSave || !btnGroup) return;

        const MAX_DIM = 800;
        const JPEG_Q = 0.85;
        let stream = null;
        let capturedB64 = null;

        function showMsg(text, color) {
            if (msgEl) {
                msgEl.style.color = color || "#555";
                msgEl.textContent = text;
            }
        }

        function stopStream() {
            if (stream) {
                stream.getTracks().forEach((t) => t.stop());
                stream = null;
            }
        }

        btnOpen.addEventListener("click", async (e) => {
            e.preventDefault();
            try {
                stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" } });
                video.srcObject = stream;
                video.style.display = "block";
                btnOpen.style.display = "none";
                btnGroup.style.display = "flex";
                btnCapture.style.display = "";
                btnRetake.style.display = "none";
                btnSave.style.display = "none";
                showMsg("Nhìn thẳng vào camera, đảm bảo đủ sáng", "#555");
            } catch (err) {
                showMsg("Không truy cập được camera: " + err.message, "#dc3545");
            }
        });

        btnCapture.addEventListener("click", (e) => {
            e.preventDefault();
            const w = video.videoWidth;
            const h = video.videoHeight;
            let sw = w;
            let sh = h;
            if (Math.max(w, h) > MAX_DIM) {
                const s = MAX_DIM / Math.max(w, h);
                sw = Math.round(w * s);
                sh = Math.round(h * s);
            }
            canvas.width = sw;
            canvas.height = sh;
            canvas.getContext("2d").drawImage(video, 0, 0, sw, sh);
            capturedB64 = canvas.toDataURL("image/jpeg", JPEG_Q).split(",")[1];
            preview.src = "data:image/jpeg;base64," + capturedB64;
            previewWrap.style.display = "block";
            stopStream();
            video.style.display = "none";
            btnCapture.style.display = "none";
            btnRetake.style.display = "";
            btnSave.style.display = "";
            showMsg("Kiểm tra ảnh — nếu OK thì bấm Lưu ảnh mẫu", "#555");
        });

        btnRetake.addEventListener("click", (e) => {
            e.preventDefault();
            capturedB64 = null;
            previewWrap.style.display = "none";
            btnOpen.click();
        });

        btnSave.addEventListener("click", async (e) => {
            e.preventDefault();
            if (!capturedB64) return;
            btnSave.disabled = true;
            showMsg("Đang xử lý...", "#555");

            const studentId = parseInt(
                window.location.pathname.split("/").filter(Boolean).pop(),
                10
            ) || null;

            try {
                const resp = await fetch("/lms/face-gate/upload-sample", {
                    method: "POST",
                    credentials: "same-origin",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        jsonrpc: "2.0",
                        method: "call",
                        id: 1,
                        params: { image: capturedB64, student_id: studentId },
                    }),
                });
                const raw = await resp.text();
                const parsed = JSON.parse(raw);
                const result = parsed.result || parsed;

                if (result.success) {
                    showMsg(
                        "Ảnh mẫu đã lưu thành công! Reload trang để xem trạng thái.",
                        "#28a745"
                    );
                    previewWrap.style.display = "none";
                    btnGroup.style.display = "none";
                } else {
                    showMsg("Lỗi: " + (result.error || "Không xác định"), "#dc3545");
                    btnSave.disabled = false;
                }
            } catch (err) {
                showMsg("Lỗi kết nối: " + err.message, "#dc3545");
                btnSave.disabled = false;
            }
        });
    },
});

