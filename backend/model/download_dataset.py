from huggingface_hub import snapshot_download

print("Downloading ISL 40-word dataset...")
print("Please wait...")

snapshot_download(
    repo_id="vidit031/isl-isolated-40words",
    repo_type="dataset",
    local_dir="ISL_DATASET"
)

print()
print("====================================")
print("ISL DATASET DOWNLOAD COMPLETED")
print("====================================")