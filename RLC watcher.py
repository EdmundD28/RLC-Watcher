import time
import webbrowser
import requests
import winsound

POLL_INTERVAL_SECONDS = 2
RATE_LIMIT_RETRY_SECONDS = 2

PRODUCT_JSON = (
    # Link for RLC ferrari F40
    # Change it to the product you want to watch.
    "https://au.creations.mattel.com/products/"
    "mattel-creations-hot-wheels-rlc-exclusive-ferrari-f40.js"

    # Test link for RLC 1985 Audi Sport Quattro S1 
    # "https://au.creations.mattel.com/products/"
    # "hot-wheels-rlc-exclusive-1985-audi-sport-quattro-s1-87492678954.js"
)

# The variant ID for the RLC Ferrari F40 is 51154648989919. 
VARIANT_ID = 51154648989919

# TESTING: The variant ID for the RLC 1985 Audi Sport Quattro S1 is 50512676487391.
# VARIANT_ID = 50512676487391

ADD_TO_CART_URL = (
    "https://au.creations.mattel.com/cart/add"
    f"?id={VARIANT_ID}&quantity=2"
)

CHECKOUT_URL = (
    # Shopify cart permalinks go directly to checkout by default.
    # Format: /cart/<variant_id>:<quantity>
    "https://au.creations.mattel.com/cart/"
    f"{VARIANT_ID}:2"
)

def create_session():
    new_session = requests.Session()
    new_session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/139.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json,text/javascript,*/*;q=0.8",
        "Connection": "keep-alive",
    })
    return new_session


session = create_session()

while True:
    try:
        r = session.get(
            PRODUCT_JSON,
            # Allow a slow TLS connection without adding any polling delay
            # when the server is responding normally.
            timeout=(10, 10),
        )

        if r.status_code == 429:
            print(
                "⚠️ RATE LIMITED — retrying in",
                RATE_LIMIT_RETRY_SECONDS,
                "seconds"
            )
            time.sleep(RATE_LIMIT_RETRY_SECONDS)
            continue

        if r.status_code == 430:
            print("🚫 SHOPIFY SECURITY REJECTION — stopping")
            break

        r.raise_for_status()

        product = r.json()

        variant = next(
            v for v in product["variants"]
            if v["id"] == VARIANT_ID
        )

        available = variant["available"]

        print(
            time.strftime("%H:%M:%S"),
            "available =", available
        )

        if available:
            # Launch both paths without waiting: one normal cart tab and one
            # direct-checkout tab. Alerts run only after both are triggered.
            triggered_at = time.perf_counter()
            webbrowser.open_new_tab(ADD_TO_CART_URL)
            webbrowser.open_new_tab(CHECKOUT_URL)
            print(
                time.strftime("%H:%M:%S"),
                "cart and checkout tabs triggered in "
                f"{time.perf_counter() - triggered_at:.6f}s"
            )

            for _ in range(5):
                winsound.Beep(1800, 250)

            break

    except (requests.exceptions.ConnectTimeout,
            requests.exceptions.ConnectionError) as e:
        print("Connection failed; rebuilding session and retrying immediately:", e)
        session.close()
        session = create_session()

    except requests.exceptions.ReadTimeout as e:
        print("Mattel connected but did not respond; retrying immediately:", e)

    except Exception as e:
        print("Check failed:", e)

    # Avoid a tight request loop that triggers Shopify rate limiting and makes
    # the watcher blind while stock is changing.
    time.sleep(POLL_INTERVAL_SECONDS)
