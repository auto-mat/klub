urls = {
    "regular_wp":              "/registrace/",
    "thanks_wp":               "/dekujeme/",
}

def wp_reverse(name):
    return urls[name]
