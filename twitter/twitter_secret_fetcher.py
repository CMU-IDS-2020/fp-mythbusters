# If you want to use this then you need to create a twitter developer account
# and create a file called "twitter_secrets.txt" with your API keys. It should look like this
#
# API_KEY=<API-KEY>
# API_SECRET_KEY=<API_SECRET_KEY>
# ACCESS_TOKEN=<ACCESS_TOKEN>
# ACCESS_TOKEN_SECRET=<ACCESS_TOKEN_SECRET>
#
# Or just talk to Joe to borrow his


secret_cache = {}


# There's probably a more pythonic way of reading in properties, but this is good enough
# Also we'll end up opening and closing the file for each secret, which is not great but w.e.
def get_secret(secret_name):
    if secret_name in secret_cache:
        return secret_cache[secret_name]

    with open("twitter_secrets.txt") as f:
        for line in f.readlines():
            if line.startswith(secret_name):
                # hopefully no api key has an '=' in it otherwise this needs to change
                secret = line.split("=")[1].strip()
                secret_cache[secret_name] = secret
                return secret
    return ""


def get_api_key():
    return get_secret("API_KEY")


def get_api_secret_key():
    return get_secret("API_SECRET_KEY")


def get_access_token():
    return get_secret("ACCESS_TOKEN")


def get_access_token_secret():
    return get_secret("ACCESS_TOKEN_SECRET")
