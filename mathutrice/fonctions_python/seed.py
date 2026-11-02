"""Seed the database with the notions and competences of the referentiel.

Run from the repository root: python -m mathutrice.fonctions_python.seed
Idempotent: rows that already exist are left alone.
"""

from uuid import NAMESPACE_URL, uuid5

from sqlmodel import Session, SQLModel, select

from mathutrice import models
from mathutrice.database import engine
from mathutrice.referentiel import REFERENTIEL


def _uuid(kind: str, key: str):
    # Deterministic, so a re-seed (or a second machine) yields the same ids.
    return uuid5(NAMESPACE_URL, f"mathutrice:{kind}:{key}")


def seed() -> tuple[int, int]:
    SQLModel.metadata.create_all(engine)
    new_notions = new_competences = 0

    with Session(engine) as session:
        for notion_key, notion_data in REFERENTIEL.items():
            notion = session.exec(
                select(models.Notion).where(
                    models.Notion.referentiel_key == notion_key
                )
            ).first()
            if notion is None:
                notion = models.Notion(
                    notion_id=_uuid("notion", notion_key),
                    referentiel_key=notion_key,
                    title=notion_data["notion_nom"],
                    description=notion_data["notion_nom"],
                )
                session.add(notion)
                new_notions += 1

            for comp in notion_data["competences"]:
                exists = session.exec(
                    select(models.Competence).where(
                        models.Competence.referentiel_code == comp["code"]
                    )
                ).first()
                if exists is None:
                    session.add(
                        models.Competence(
                            competence_id=_uuid("competence", comp["code"]),
                            referentiel_code=comp["code"],
                            title=comp["nom"],
                            level=comp["niveau"],
                            notion_id=notion.notion_id,
                        )
                    )
                    new_competences += 1
        session.commit()

    return new_notions, new_competences


if __name__ == "__main__":
    notions, competences = seed()
    print(f"Seeded {notions} notions and {competences} competences.")
