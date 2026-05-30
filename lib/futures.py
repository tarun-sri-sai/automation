import tempfile
import os
import shutil
import time
import sys


def clear_temp():
    print("Cleaning up temp directory")
    temp_dir = tempfile.gettempdir()
    failed_count = 0
    for item in os.listdir(temp_dir):
        item_path = os.path.join(temp_dir, item)

        try:
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.unlink(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
        except Exception:
            failed_count += 1
    if failed_count:
        print(f"Failed to delete {failed_count} items from temp directory")


def await_futures(executor, function, round, rounds, round_idx,
                  wait_time, batches_per_round, batch_size):
    print(f"Batches: {len(round)}, Round: {round_idx + 1}/{rounds}, "
          f"Batches per round: {batches_per_round}")

    futures = [executor.submit(function, file_batch) for file_batch in round]
    try:
        for future in futures:
            future.result()
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt detected. Cancelling tasks...")
        for future in futures:
            future.cancel()
        executor.shutdown(wait=False)
        sys.exit(0)

    if round_idx < rounds - 1 and wait_time > 0:
        print(f"Processed batch {round_idx + 1} of max "
              f"{batches_per_round * batch_size} items. "
              f"Waiting for {wait_time} seconds")
        time.sleep(wait_time)

    if (half_rounds := rounds / 2) <= rounds <= half_rounds + 1:
        clear_temp()
