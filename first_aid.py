import pandas as pd
import os


def load_first_aid():
    try:
        file_path = os.path.join(
            os.path.dirname(__file__),
            "first_aid.csv"
        )
        return pd.read_csv(file_path)

    except Exception as e:
        print("CSV Load Error:", e)
        return None


def get_first_aid(issue, lang="en"):
    try:
        df = load_first_aid()

        if df is None:
            return "⚠️ First aid data not available"

        df["issue"] = (
            df["issue"]
            .astype(str)
            .str.lower()
            .str.strip()
        )

        issue = str(issue).lower().strip()

        alias = {
            "cardiology": [
                "cardiology",
                "heart",
                "heart attack",
                "chest pain"
            ],
            "neuro": [
                "neuro",
                "stroke",
                "brain",
                "seizure",
                "unconscious",
                "head injury",
                "head pain"
            ],
            "respiratory": [
                "respiratory",
                "breathing problem",
                "breathing",
                "asthma attack",
                "asthma",
                "shortness of breath"
            ],
            "emergency": [
                "emergency",
                "accident",
                "bleeding",
                "burn",
                "fracture",
                "poison",
                "overdose",
                "electric shock",
                "drowning",
                "snake bite",
                "dog bite",
                "spinal injury"
            ],
            "general": [
                "general",
                "fever high",
                "vomiting severe",
                "diarrhea severe",
                "panic attack",
                "heat stroke",
                "hypothermia"
            ]
        }

        # 1. direct exact match first
        exact = df[df["issue"] == issue]
        if not exact.empty:
            return format_output(
                get_lang(exact.iloc[0], lang)
            )

        search_terms = [issue]

        for key, values in alias.items():
            if issue == key or issue in values:
                search_terms.extend(values)

        search_terms = list(set(search_terms))

        # 2. contains match
        for term in search_terms:
            result = df[
                df["issue"].str.contains(
                    term,
                    na=False,
                    regex=False
                )
            ]

            if not result.empty:
                row = result.iloc[0]
                return format_output(
                    get_lang(row, lang)
                )

        # 3. fallback partial match
        for i in df["issue"]:
            for term in search_terms:
                if term in i or i in term:
                    row = df[df["issue"] == i]

                    if not row.empty:
                        return format_output(
                            get_lang(row.iloc[0], lang)
                        )

        return """
⚠️ No first aid found.

Go to nearest hospital immediately.
"""

    except Exception as e:
        print("First Aid Error:", e)
        return """
⚠️ First aid system error
"""


def get_lang(row, lang):
    try:
        if lang == "te":
            return row["first_aid_te"]

        elif lang == "hi":
            return row["first_aid_hi"]

        else:
            return row["first_aid_en"]

    except:
        try:
            return row["first_aid"]
        except:
            return "No first aid available"


def format_output(text):
    text = str(text)

    if "," in text:
        points = text.split(",")

    elif "\n" in text:
        points = text.split("\n")

    else:
        points = [text]

    formatted = ""

    for p in points:
        p = p.strip()

        if p:
            formatted += f"• {p}\n"

    return formatted.strip()


if __name__ == "__main__":
    print(get_first_aid("heart attack"))
    print(get_first_aid("stroke"))
    print(get_first_aid("cardiology", "te"))