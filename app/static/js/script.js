const fileInput = document.getElementById("file-input");
const uploadBtn = document.getElementById("upload-btn");
const fileRows = document.getElementById("files");
const trashRows = document.getElementById("trash-files");
const storageInfo = document.getElementById("storage-info");
const searchInput = document.getElementById("search");
const myDrivesTab = document.getElementById("my-drives-tab");
const trashTab = document.getElementById("trash-tab");
const myDrivesSection = document.getElementById("my-drives-section");
const trashSection = document.getElementById("trash-section");
const searchTrashInput = document.getElementById("search-trash");
const sharedTab = document.getElementById("shared-tab");
const sharedSection = document.getElementById("shared-section");
const sharedFilesBody = document.getElementById("shared-files");
const searchSharedInput = document.getElementById("search-shared");
const sharedByTab = document.getElementById("shared-by-tab");
const sharedBySection = document.getElementById("shared-by-section");
const sharedByFilesBody = document.getElementById("shared-by-files");
const searchSharedByInput = document.getElementById("search-shared-by");
const uploadProgressDiv = document.getElementById("upload-progress");

function updateStorageInfo() {
    storageInfo.innerHTML = `Storage: <strong>${currentStorage.toFixed(2)} / ${maxStorage.toFixed(2)} MB</strong>`;
}

document.addEventListener("DOMContentLoaded", () => {
    updateStorageInfo();
    loadFiles("active");
});

uploadBtn.addEventListener("click", () => fileInput.click());

//fileInput.addEventListener("change", function () {
//    let file = fileInput.files[0];
//    if (file) {
//        let fileSizeInMB = file.size / (1024 * 1024);
//        if (currentStorage + fileSizeInMB > maxStorage) {
//            showCustomAlert("Not enough storage");
//            return;
//        }
//
//        const formData = new FormData();
//        formData.append("file", file);
//
//        fetch("/upload", {
//            method: "POST",
//            body: formData,
//        })
//        .then(res => res.json())
//        .then(data => {
//            if (data.status === "success") {
//                currentStorage += fileSizeInMB;
//                updateStorageInfo();
//                loadFiles("active");
//            } else {
//                showCustomAlert(data.message || "Upload failed");
//            }
//        })
//        .catch(error => showCustomAlert("Upload failed"));
//    }
//});

fileInput.addEventListener("change", function () {
    const files = Array.from(fileInput.files);
    if (files.length === 0) return;

    uploadMultiFiles(files);
    this.value = '';
});

function uploadMultiFiles(files) {
    if (files.length === 0) {
        loadFiles("active");
        uploadProgressDiv.style.display = "none"; // Hide progress
        return;
    }

    uploadProgressDiv.style.display = "inline"; // Show progress
    uploadProgressDiv.innerText = `Uploading (${files.length}) files...`;

    const file = files.shift();
    let fileSizeInMB = file.size / (1024 * 1024);

    if (currentStorage + fileSizeInMB > maxStorage) {
        showCustomAlert(`Not enough storage for file ${file.name}`);
        uploadMultiFiles(files);
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    fetch("/upload", {
        method: "POST",
        body: formData,
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "success") {
            currentStorage += fileSizeInMB;
            updateStorageInfo();
        } else {
            showCustomAlert(data.message || `Upload failed: ${file.name}`);
        }
        uploadMultiFiles(files);
    })
    .catch(() => {
        showCustomAlert(`Upload failed: ${file.name}`);
        uploadMultiFiles(files);
    });
}

function loadFiles(view = "active") {
    fetch(`/list-files?view=${view}`)
        .then(res => res.json())
        .then(data => {
            if (data.status === "success") {
                if (view === "active") showMyDrives(data.files);
                else showTrash(data.files);
            } else {
                showCustomAlert(data.message || "Failed to load files.");
            }
        })
        .catch(() => showCustomAlert("Failed to load files."));
}

function showMyDrives(files) {
    fileRows.innerHTML = "";
    files.forEach(file => {
        let extension = "Unknown";
            if (file.filename.includes(".")) {
                extension = file.filename.split('.').pop().toUpperCase();
            }
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${file.filename}</td>
            <td>${extension}</td>
            <td>${file.size_mb.toFixed(2)} MB</td>
            <td>${file.upload_date}</td>
            <td>
                <a class="btn btn-sm btn-success" href="/download-file?filename=${file.filename}">Download</a>
                <a class="btn btn-sm btn-warning rename-btn" href="#">Rename</a>
                <a class="btn btn-sm btn-success share-btn" href="#">Share</a>
                <button class="delete-btn">Delete</button>
            </td>
        `;
        row.querySelector(".delete-btn").addEventListener("click", () => {
            showConfirmDialog("Are you sure you want to delete this file?", confirmed => {
                if (confirmed) {
                    fetch("/delete-file", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ filename: file.filename })
                    })
                    .then(res => res.json())
                    .then(() => loadFiles("active"));
                }
            });
        });
        row.querySelector(".share-btn").addEventListener("click", () => {
            showSharePopup(file.filename);
        });
        row.querySelector(".rename-btn").addEventListener("click", () => {
            showRenamePopup(file.filename);
        });
        fileRows.appendChild(row);
    });
}

function showTrash(files) {
    trashRows.innerHTML = "";
    files.forEach(file => {
        let extension = "Unknown";
            if (file.filename.includes(".")) {
                extension = file.filename.split('.').pop().toUpperCase();
            }
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${file.filename}</td>
            <td>${extension}</td>
            <td>${file.size_mb.toFixed(2)} MB</td>
            <td>${file.upload_date}</td>
            <td>
                <button class="restore-btn">Restore</button>
                <button class="permanent-delete-btn">Delete Permanently</button>
            </td>
        `;
        row.querySelector(".restore-btn").addEventListener("click", () => {
            fetch("/restore-file", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ filename: file.filename })
            })
            .then(res => res.json())
            .then(data => {
                if (data.status === "success") {
                    loadFiles("active");
                    loadFiles("trash");
                    updateStorageInfo();
                } else {
                    showCustomAlert(data.message || "Restore failed.");
                }
            });
        });
        row.querySelector(".permanent-delete-btn").addEventListener("click", () => {
            showConfirmDialog("Permanently delete this file?", (confirmed) => {
                if (confirmed) {
                    fetch("/delete-permanently", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ filename: file.filename })
                    })
                    .then(res => res.json())
                    .then(data => {
                        if (data.status === "success") {
                            currentStorage -= file.size_mb;
                            if (currentStorage < 0) currentStorage = 0;
                            loadFiles("trash");
                            updateStorageInfo();
                        } else {
                            showCustomAlert(data.message || "Delete failed");
                        }
                    });
                }
            });
        });
        trashRows.appendChild(row);
    });
}

searchInput.addEventListener("input", () => {
    const query = searchInput.value.toLowerCase();
    Array.from(fileRows.getElementsByTagName("tr")).forEach((row) => {
        row.style.display = row.textContent.toLowerCase().includes(query) ? "" : "none";
    });
});

searchTrashInput.addEventListener("input", () => {
    const query = searchTrashInput.value.toLowerCase();
    Array.from(trashRows.getElementsByTagName("tr")).forEach((row) => {
        row.style.display = row.textContent.toLowerCase().includes(query) ? "" : "none";
    });
});

myDrivesTab.addEventListener("click", (e) => {
    e.preventDefault();
    myDrivesSection.style.display = "block";
    trashSection.style.display = "none";
    sharedSection.style.display = "none";
    sharedBySection.style.display = "none";
    loadFiles("active");
});

trashTab.addEventListener("click", (e) => {
    e.preventDefault();
    trashSection.style.display = "block";
    myDrivesSection.style.display = "none";
    sharedSection.style.display = "none";
    sharedBySection.style.display = "none";
    loadFiles("trash");
});

function showCustomAlert(message) {
    const alertBox = document.createElement("div");
    alertBox.className = "custom-alert";
    alertBox.innerHTML = `
        <div class="custom-alert-content">
            <h2>⚠️ Warning</h2>
            <p>${message}</p>
            <button id="close-alert">OK</button>
        </div>
    `;
    document.body.appendChild(alertBox);
    document.getElementById("close-alert").addEventListener("click", () => {
        document.body.removeChild(alertBox);
    });
}

function showConfirmDialog(message, callback) {
    const confirmBox = document.createElement("div");
    confirmBox.className = "custom-alert";
    confirmBox.innerHTML = `
        <div class="custom-alert-content">
            <h2>🔍 Confirmation</h2>
            <p>${message}</p>
            <button id="confirm-yes">Yes</button>
            <button id="confirm-no">No</button>
        </div>
    `;
    document.body.appendChild(confirmBox);
    document.getElementById("confirm-yes").addEventListener("click", () => {
        callback(true);
        document.body.removeChild(confirmBox);
    });
    document.getElementById("confirm-no").addEventListener("click", () => {
        callback(false);
        document.body.removeChild(confirmBox);
    });
}

sharedTab.addEventListener("click", (e) => {
    e.preventDefault();
    myDrivesSection.style.display = "none";
    trashSection.style.display = "none";
    sharedSection.style.display = "block";
    sharedBySection.style.display = "none";
    loadSharedFiles();
});

function loadSharedFiles() {
    fetch("/list-shared-files")
        .then(res => res.json())
        .then(data => {
            if (data.status === "success") {
                sharedFilesBody.innerHTML = "";
                data.files.forEach(file => {
                    const row = document.createElement("tr");
                    row.innerHTML = `
                        <td>${file.filename}</td>
                        <td>${file.owner}</td>
                        <td>${file.size_mb.toFixed(2)} MB</td>
                        <td>${file.upload_date}</td>
                        <td>
                            <a class="btn btn-sm btn-success" href="/download-file?filename=${file.filename}&owner=${file.owner}">Download</a>
                        </td>
                    `;
                    sharedFilesBody.appendChild(row);
                });
            } else {
                showCustomAlert(data.message || "Failed to load shared files.");
            }
        })
        .catch(() => showCustomAlert("Failed to load shared files."));
}

function showSharePopup(filename) {
    const shareBox = document.createElement("div");
    shareBox.className = "custom-alert";
    shareBox.innerHTML = `
        <div class="custom-alert-content">
            <h2>📤 Share File</h2>
            <p>Enter username to share <strong>${filename}</strong> with:</p>
            <input type="text" id="recipient-input" placeholder="Recipient username">
            <div style="margin-top: 1em;">
                <button id="share-confirm-btn">Share</button>
                <button id="unshare-btn">Unshare</button>
                <button id="share-cancel-btn">Cancel</button>
            </div>
        </div>
    `;
    document.body.appendChild(shareBox);

    document.getElementById("share-cancel-btn").addEventListener("click", () => {
        document.body.removeChild(shareBox);
    });

    document.getElementById("share-confirm-btn").addEventListener("click", () => {
        const recipient = document.getElementById("recipient-input").value.trim();
        if (!recipient) {
            showCustomAlert("Please enter a username.");
            return;
        }

        fetch("/share-file", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ filename, recipient })
        })
        .then(res => res.json())
        .then(data => {
            document.body.removeChild(shareBox);
            if (data.status === "success") {
                showCustomAlert("File shared successfully.");
            } else {
                showCustomAlert(data.message || "Failed to share file.");
            }
        })
        .catch(() => {
            document.body.removeChild(shareBox);
            showCustomAlert("Failed to share file.");
        });
    });

    document.getElementById("unshare-btn").addEventListener("click", () => {
        const recipient = document.getElementById("recipient-input").value.trim();
        if (!recipient) {
            showCustomAlert("Please enter a username.");
            return;
        }

        fetch("/unshare-file", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ filename, recipient })
        })
        .then(res => res.json())
        .then(data => {
            document.body.removeChild(shareBox);
            if (data.status === "success") {
                showCustomAlert("File unshared successfully.");
            } else {
                showCustomAlert(data.message || "Failed to unshare file.");
            }
        })
        .catch(() => {
            document.body.removeChild(shareBox);
            showCustomAlert("Failed to unshare file.");
        });
    });
}

searchSharedInput.addEventListener("input", () => {
    const query = searchSharedInput.value.toLowerCase();
    Array.from(sharedFilesBody.getElementsByTagName("tr")).forEach((row) => {
        row.style.display = row.textContent.toLowerCase().includes(query) ? "" : "none";
    });
});

sharedByTab.addEventListener("click", (e) => {
    e.preventDefault();
    myDrivesSection.style.display = "none";
    trashSection.style.display = "none";
    sharedSection.style.display = "none";
    sharedBySection.style.display = "block";
    loadSharedByMe();
});

function loadSharedByMe() {
    fetch("/shared-by-me")
        .then(res => res.json())
        .then(data => {
            if (data.status === "success") {
                sharedByFilesBody.innerHTML = "";
                data.files.forEach(file => {
                    const row = document.createElement("tr");
                    row.innerHTML = `
                        <td>${file.filename}</td>
                        <td>${file.recipients.join(", ")}</td>
                    `;
                    sharedByFilesBody.appendChild(row);
                });
            } else {
                showCustomAlert(data.message || "Failed to load shared-by-me list.");
            }
        })
        .catch(() => showCustomAlert("Failed to load shared-by-me list."));
}

searchSharedByInput.addEventListener("input", () => {
    const query = searchSharedByInput.value.toLowerCase();
    Array.from(sharedByFilesBody.getElementsByTagName("tr")).forEach((row) => {
        row.style.display = row.textContent.toLowerCase().includes(query) ? "" : "none";
    });
});

function showRenamePopup(oldFilename) {
    const renameBox = document.createElement("div");
    renameBox.className = "custom-alert";
    renameBox.innerHTML = `
        <div class="custom-alert-content">
            <h2>Rename File</h2>
            <p>Enter new name for <strong>${oldFilename}</strong>:</p>
            <input type="text" id="new-filename-input" placeholder="New filename">
            <div style="margin-top: 1em;">
                <button id="rename-confirm-btn">Rename</button>
                <button id="rename-cancel-btn">Cancel</button>
            </div>
        </div>
    `;
    document.body.appendChild(renameBox);

    document.getElementById("rename-cancel-btn").addEventListener("click", () => {
        document.body.removeChild(renameBox);
    });

    document.getElementById("rename-confirm-btn").addEventListener("click", () => {
        const newFilename = document.getElementById("new-filename-input").value.trim();
        if (!newFilename) {
            showCustomAlert("Please enter a new filename.");
            return;
        }

        fetch("/rename-file", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ old_filename: oldFilename, new_filename: newFilename })
        })
        .then(res => res.json())
        .then(data => {
            document.body.removeChild(renameBox);
            if (data.status === "success") {
                showCustomAlert("File renamed successfully.");
                loadFiles("active");
            } else {
                showCustomAlert(data.message || "Failed to rename file.");
            }
        })
        .catch(() => {
            document.body.removeChild(renameBox);
            showCustomAlert("Failed to rename file.");
        });
    });
}
