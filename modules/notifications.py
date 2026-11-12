from winotify import Notification, audio


def send_notification(title, message):
    try:
        notification = Notification(
            app_id="Min Planerare",
            title=title,
            msg=message,
            duration="short"
        )

        notification.set_audio(
            audio.Default,
            loop=False
        )

        notification.show()

    except Exception as error:
        print("Kunde inte visa notis:", error)
