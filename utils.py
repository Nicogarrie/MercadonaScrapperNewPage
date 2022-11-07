def get_already_saved_ids():
    with open(r'saved_ids.txt', 'r') as file:
        return file.read().split('\n')


def get_failed_ids():
    with open(r'failed_image_ids.txt', 'r') as file:
        return file.read().split('\n')


def store_already_saved_ids(ids):
    with open(r'saved_ids.txt', 'a') as file:
        file.write("\n")
        file.write('\n'.join(ids))


def store_failed_id(identifier):
    with open(r'failed_image_ids.txt', 'a') as file:
        file.write("\n")
        file.write('\n'.join([identifier]))


def check_id_already_saved(identifier):
    global saved_ids
    if identifier in saved_ids:
        return True
    return False


def check_id_already_failed(identifier):
    global failed_image_ids
    if identifier in failed_image_ids:
        return True
    return False


saved_ids = get_already_saved_ids()
failed_image_ids = get_failed_ids()
