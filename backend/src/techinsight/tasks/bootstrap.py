from __future__ import annotations

import json

from techinsight.application.bootstrap import BootstrapService
from techinsight.config.settings import get_settings
from techinsight.infrastructure.db import SessionLocal
from techinsight.infrastructure.embeddings.factory import build_embedding_provider


def main() -> None:
    settings = get_settings()
    provider = build_embedding_provider(settings)
    with SessionLocal() as session:
        service = BootstrapService(session=session, settings=settings, embedding_provider=provider)
        summary = service.run()
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
