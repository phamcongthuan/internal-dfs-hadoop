from flask import render_template, request, redirect, url_for, flash, session, jsonify, send_file
import os
from app import app, db
from app.models import User, File, SharedFile
from app.auth import auth_bp
from app.utils import upload_to_hdfs, delete_hdfs_file, download_from_hdfs, rename_hdfs_file
from datetime import datetime
from decimal import Decimal
from werkzeug.security import check_password_hash, generate_password_hash

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.register_blueprint(auth_bp)

@app.route("/")
def root():
    return redirect(url_for("auth.login"))

@app.route("/home")
def home():
    username = session.get("username")
    if not username:
        flash("You must log in first.")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(username=username).first()
    if not user:
        flash("User not found.")
        return redirect(url_for("auth.login"))

    return render_template("index.html",
                           username=user.username,
                           used_storage=user.used_storage,
                           storage_limit=user.storage_limit)

def generate_unique_filename(username, original_name):
    base, ext = os.path.splitext(original_name)
    i = 1
    new_name = original_name
    while File.query.filter_by(username=username, filename=new_name).first():
        new_name = f"{base}({i}){ext}"
        i += 1
    return new_name

@app.route("/upload", methods=["POST"])
def upload_file():
    if "username" not in session:
        return jsonify({"status": "error", "message": "Not logged in"}), 401

    file = request.files.get("file")
    if not file:
        return jsonify({"status": "error", "message": "No file"}), 400

    username = session["username"]
    original_name = file.filename
    filename = generate_unique_filename(username, original_name)

    local_path = os.path.join(UPLOAD_FOLDER, filename)
    hdfs_path = f"/user/phamcongthuan/{username}/{filename}"

    try:
        file.save(local_path)
        upload_to_hdfs(local_path, hdfs_path)

        file_size_mb = os.path.getsize(local_path) / (1024 * 1024)

        user = User.query.filter_by(username=username).first()
        user.used_storage += Decimal(str(file_size_mb))

        new_file = File(
            filename=filename,
            username=username,
            size_mb=file_size_mb,
            upload_date=datetime.utcnow(),
            is_deleted=False
        )
        db.session.add(new_file)
        db.session.commit()

        return jsonify({"status": "success"})

    except Exception as e:
        print("UPLOAD FAILED:", e)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/delete-file", methods=["POST"])
def delete_file():
    if "username" not in session:
        return jsonify({"status": "error"}), 401

    data = request.get_json()
    filename = data.get("filename")
    username = session["username"]

    try:
        file = File.query.filter_by(username=username, filename=filename, is_deleted=False).first()
        if not file:
            return jsonify({"status": "error", "message": "File not found"}), 404

        file.is_deleted = True
        db.session.commit()

        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/restore-file", methods=["POST"])
def restore_file():
    if "username" not in session:
        return jsonify({"status": "error"}), 401

    data = request.get_json()
    filename = data.get("filename")
    username = session["username"]

    try:
        file = File.query.filter_by(username=username, filename=filename, is_deleted=True).first()
        if not file:
            return jsonify({"status": "error", "message": "File not found in trash"}), 404

        user = User.query.filter_by(username=username).first()
        # if user.used_storage + file.size_mb > user.storage_limit:
        #     return jsonify({"status": "error", "message": "Not enough storage to restore"}), 400
        if user.used_storage + Decimal(str(file.size_mb)) > Decimal(str(user.storage_limit)):
            return jsonify({"status": "error", "message": "Not enough storage to restore"}), 400

        file.is_deleted = False
        db.session.commit()

        return jsonify({"status": "success"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/list-files", methods=["GET"])
def list_files():
    if "username" not in session:
        return jsonify({"status": "error", "message": "Not logged in"}), 401

    username = session["username"]
    view = request.args.get("view", "active")

    try:
        if view == "trash":
            files = File.query.filter_by(username=username, is_deleted=True).all()
        else:
            files = File.query.filter_by(username=username, is_deleted=False).all()

        file_list = [{
            "filename": f.filename,
            "size_mb": round(f.size_mb, 2),
            "upload_date": f.upload_date.strftime("%d/%m/%Y")
        } for f in files]

        return jsonify({"status": "success", "files": file_list})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/download-file")
def download_file():
    if "username" not in session:
        return "Not logged in", 401

    filename = request.args.get("filename")
    owner_username = request.args.get("owner") or session["username"]

    try:
        local_path = os.path.join(UPLOAD_FOLDER, filename)
        hdfs_path = f"/user/phamcongthuan/{owner_username}/{filename}"

        download_from_hdfs(hdfs_path, local_path)
        return send_file(local_path, as_attachment=True)
    except Exception as e:
        return f"Error: {e}", 500

@app.route("/delete-permanently", methods=["POST"])
def delete_permanently():
    if "username" not in session:
        return jsonify({"status": "error"}), 401

    data = request.get_json()
    filename = data.get("filename")
    username = session["username"]

    try:
        file = File.query.filter_by(username=username, filename=filename, is_deleted=True).first()
        if not file:
            return jsonify({"status": "error", "message": "File not found in trash"}), 404

        hdfs_path = f"/user/phamcongthuan/{username}/{filename}"
        delete_hdfs_file(hdfs_path)

        user = User.query.filter_by(username=username).first()
        user.used_storage = max(Decimal("0"), user.used_storage - Decimal(str(file.size_mb)))

        SharedFile.query.filter_by(file_id=file.id).delete()
        db.session.delete(file)
        db.session.commit()

        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/share-file", methods=["POST"])
def share_file():
    username = session.get("username")
    if not username:
        return jsonify({"status": "error", "message": "Not logged in"}), 401

    data = request.get_json()
    filename = data.get("filename")
    recipient_username = data.get("recipient")

    if not filename or not recipient_username:
        return jsonify({"status": "error", "message": "Missing data"}), 400

    owner = User.query.filter_by(username=username).first()
    recipient = User.query.filter_by(username=recipient_username).first()
    if not recipient:
        return jsonify({"status": "error", "message": "Recipient not found"}), 404

    file = File.query.filter_by(filename=filename, username=username, is_deleted=False).first()
    if not file:
        return jsonify({"status": "error", "message": "File not found"}), 404

    # Check if already shared
    existing = SharedFile.query.filter_by(file_id=file.id, recipient_id=recipient.id).first()
    if existing:
        return jsonify({"status": "error", "message": "File already shared with this user"}), 400

    shared = SharedFile(file_id=file.id, owner_id=owner.id, recipient_id=recipient.id)
    db.session.add(shared)
    db.session.commit()

    return jsonify({"status": "success"})

@app.route("/list-shared-files", methods=["GET"])
def list_shared_files():
    if "username" not in session:
        return jsonify({"status": "error", "message": "Not logged in"}), 401

    username = session["username"]
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    try:
        shared_entries = SharedFile.query.filter_by(recipient_id=user.id).all()

        shared_files = []
        for entry in shared_entries:
            if not entry.file.is_deleted:
                shared_files.append({
                    "filename": entry.file.filename,
                    "size_mb": round(entry.file.size_mb, 2),
                    "upload_date": entry.file.upload_date.strftime("%d/%m/%Y"),
                    "owner": entry.owner.username
                })

        return jsonify({"status": "success", "files": shared_files})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/unshare-file", methods=["POST"])
def unshare_file():
    username = session.get("username")
    if not username:
        return jsonify({"status": "error", "message": "Not logged in"}), 401

    data = request.get_json()
    filename = data.get("filename")
    recipient_username = data.get("recipient")

    if not filename or not recipient_username:
        return jsonify({"status": "error", "message": "Missing data"}), 400

    owner = User.query.filter_by(username=username).first()
    recipient = User.query.filter_by(username=recipient_username).first()
    if not recipient:
        return jsonify({"status": "error", "message": "Recipient not found"}), 404

    file = File.query.filter_by(filename=filename, username=username, is_deleted=False).first()
    if not file:
        return jsonify({"status": "error", "message": "File not found"}), 404

    shared = SharedFile.query.filter_by(file_id=file.id, owner_id=owner.id, recipient_id=recipient.id).first()
    if not shared:
        return jsonify({"status": "error", "message": "This file is not shared with this user."}), 400

    db.session.delete(shared)
    db.session.commit()
    return jsonify({"status": "success"})

@app.route("/shared-by-me", methods=["GET"])
def shared_by_me():
    if "username" not in session:
        return jsonify({"status": "error", "message": "Not logged in"}), 401

    username = session["username"]
    user = User.query.filter_by(username=username).first()

    try:
        shared_entries = SharedFile.query.filter_by(owner_id=user.id).all()
        result = {}

        for entry in shared_entries:
            if not entry.file.is_deleted:
                fname = entry.file.filename
                if fname not in result:
                    result[fname] = []
                result[fname].append(entry.recipient.username)

        shared_files = [{"filename": k, "recipients": v} for k, v in result.items()]
        return jsonify({"status": "success", "files": shared_files})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/change-password", methods=["GET", "POST"])
def change_password():
    if "username" not in session:
        flash("You must log in first.")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if not current_password or not new_password or not confirm_password:
            flash("Please fill out all fields.")
            return redirect(url_for("change_password"))

        user = User.query.filter_by(username=session["username"]).first()

        if not check_password_hash(user.password, current_password):
            flash("Current password is incorrect.")
            return redirect(url_for("change_password"))

        if new_password != confirm_password:
            flash("New passwords do not match.")
            return redirect(url_for("change_password"))

        user.password = generate_password_hash(new_password)
        db.session.commit()
        return redirect(url_for("home"))

    return render_template("change_password.html")

@app.route("/rename-file", methods=["POST"])
def rename_file():
    if "username" not in session:
        return jsonify({"status": "error", "message": "Not logged in"}), 401

    data = request.get_json()
    old_filename = data.get("old_filename")
    new_filename = data.get("new_filename")
    username = session["username"]

    if not old_filename or not new_filename:
        return jsonify({"status": "error", "message": "Missing filename"}), 400

    try:
        # Find file with old name
        file = File.query.filter_by(username=username, filename=old_filename, is_deleted=False).first()
        if not file:
            return jsonify({"status": "error", "message": "File not found"}), 404

        # Check new name duplicate
        exists = File.query.filter_by(username=username, filename=new_filename).first()
        if exists:
            return jsonify({"status": "error", "message": "New filename already exists"}), 400

        # Rename in hdfs
        old_hdfs_path = f"/user/phamcongthuan/{username}/{old_filename}"
        new_hdfs_path = f"/user/phamcongthuan/{username}/{new_filename}"
        rename_hdfs_file(old_hdfs_path, new_hdfs_path)

        # Update db
        file.filename = new_filename
        db.session.commit()

        return jsonify({"status": "success"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    # app.run(debug=True)
    app.run(host='0.0.0.0', port=5000)
