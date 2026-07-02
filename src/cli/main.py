import argparse
import asyncio
from pathlib import Path

from src.sdk import ShalomCI_SDK


async def run_process(args: argparse.Namespace):
    """מריץ את תהליך בדיקת עץ המוצר (BOM) מתחילתו ועד סופו."""
    print(f"[*] מתחיל עיבוד לקובץ: {args.file_path}")

    sdk = ShalomCI_SDK()
    await sdk.initialize()

    try:
        print("[1/5] קורא עץ מוצר ומחלץ מק\"טים...")
        bom_data = await sdk.process_bom(args.file_path)
        print(f"      > זוהו {len(bom_data)} רכיבים.")

        print("[2/5] מעשיר נתונים מול ספקי הרכיבים...")
        await sdk.enrich_components(bom_data)

        print("[3/5] מחשב ציוני סיכון...")
        eval_result = await sdk.evaluate_risks(bom_data)
        print(f"      > ציון פרויקט שוקלל ל: {eval_result['project_score']}/5.0")

        print("[4/5] מאתר חלופות קרוס-רפרנס לרכיבים בסיכון ופותח תיקים במידת הצורך...")
        final_components = await sdk.find_mitigations(eval_result["components"], project_name=Path(args.file_path).stem)

        output_file = f"Report_{Path(args.file_path).name}"
        print(f"[5/5] מייצר דוח אקסל מסכם: {output_file}...")
        await sdk.generate_report(final_components, output_file)

        print("\n[V] התהליך הסתיים בהצלחה!")

    except Exception as e:
        print(f"\n[X] שגיאה במהלך העיבוד: {e}")
    finally:
        await sdk.close()


async def run_cases(args: argparse.Namespace):
    """מנהל את תיקי הטיפול של הרכיבים שהתיישנו."""
    sdk = ShalomCI_SDK()
    await sdk.initialize()

    try:
        if args.action == "list":
            print("[*] שולף תיקי טיפול פתוחים (Cases)...")
            cases = await sdk.case_manager.list_open_cases()

            if not cases:
                print("    > אין תיקים פתוחים כרגע. הפרויקטים בריאים!")
            else:
                print(f"    > נמצאו {len(cases)} תיקים הדורשים סבב הנדסי:\n")
                for c in cases:
                    print(
                        f"      - תיק #{c['id']} | פרויקט: {c['project_name']} | מק\"ט בעייתי: {c['mpn']} | תאריך פתיחה: {c['created_at']}")
        else:
            print("[X] פעולה לא מוכרת.")
    finally:
        await sdk.close()


def main():
    """נקודת הכניסה הראשית לממשק שורת הפקודה."""
    parser = argparse.ArgumentParser(description="ShalomCI - Electronic Component Lifecycle Management")
    subparsers = parser.add_subparsers(dest="command", required=True, help="פקודות המערכת")

    # פקודת process
    process_parser = subparsers.add_parser("process", help="Process a BOM file and generate risk report")
    process_parser.add_argument("file_path", help="Path to the BOM file (.xlsx or .csv)")

    # פקודת cases
    cases_parser = subparsers.add_parser("cases", help="Manage obsolete component cases")
    cases_parser.add_argument("action", choices=["list"], help="Action to perform (e.g., list)")

    args = parser.parse_args()

    if args.command == "process":
        asyncio.run(run_process(args))
    elif args.command == "cases":
        asyncio.run(run_cases(args))


if __name__ == "__main__":
    main()
