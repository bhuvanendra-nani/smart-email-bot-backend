from app.services.gmail_service import (
    get_gmail_service,
    extract_text_from_payload,
    get_header,
)


SEARCH_TERMS = [
    "Exxonmobil",
    "Sandisk",
    "Cognizant Technical Assessment",
    "Elgi Online test",
]


def recover():
    service = get_gmail_service()

    for term in SEARCH_TERMS:

        print("\n")
        print("=" * 100)
        print("SEARCH:", term)
        print("=" * 100)

        result = (
            service.users()
            .messages()
            .list(
                userId="me",
                q=f'"{term}" newer_than:6m',
                maxResults=20,
            )
            .execute()
        )

        messages = result.get("messages", [])

        print("FOUND:", len(messages))

        for msg in messages:

            message_id = msg.get("id")

            if not message_id:
                continue

            try:
                full_msg = (
                    service.users()
                    .messages()
                    .get(
                        userId="me",
                        id=message_id,
                        format="full",
                    )
                    .execute()
                )
            except Exception as error:
                print(
                    "ERROR:",
                    message_id,
                    error,
                )
                continue

            payload = full_msg.get(
                "payload",
                {},
            )

            headers = payload.get(
                "headers",
                [],
            )

            subject = get_header(
                headers,
                "Subject",
            )

            sender = get_header(
                headers,
                "From",
            )

            date = get_header(
                headers,
                "Date",
            )

            body = extract_text_from_payload(
                payload
            )

            print("\n" + "-" * 100)
            print("MESSAGE ID:", message_id)
            print("DATE:", date)
            print("FROM:", sender)
            print("SUBJECT:", subject)
            print("-" * 100)
            print(body[:5000])


if __name__ == "__main__":
    recover()