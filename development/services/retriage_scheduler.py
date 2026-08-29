import threading
import time

from services.retriage_service import check_retriage_alerts


def start_retriage_monitor(app):

    def monitor():
        print("[RE-TRIAGE] Background monitor started")

        while True:
            try:
                with app.app_context():

                    triggered_alerts = check_retriage_alerts()

                    if triggered_alerts:
                        print(
                            f"[RE-TRIAGE] "
                            f"{len(triggered_alerts)} alert(s) triggered"
                        )

            except Exception as e:
                print(
                    f"[RE-TRIAGE ERROR] {e}"
                )

            time.sleep(30)

    thread = threading.Thread(
        target=monitor,
        daemon=True,
    )

    thread.start()