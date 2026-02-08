# Core Structure Patterns

JPPT의 `src/core/` 디렉토리는 비즈니스 로직을 구현하는 공간입니다. 이 문서는 kavs 프로젝트에서 사용한 실전 구조화 패턴을 설명합니다.

## 1. 데이터 소스 패턴 (Multi-Source Integration)

여러 외부 API나 데이터 소스를 통합해야 할 때 사용하는 패턴입니다.

### 디렉토리 구조

```
src/core/data/
├── __init__.py
├── base.py              # ABC 인터페이스
├── source_a.py          # 첫 번째 데이터 소스 구현
├── source_b.py          # 두 번째 데이터 소스 구현
└── aggregator.py        # 멀티소스 통합 로직
```

### 예제: base.py (ABC 인터페이스)

```python
"""Base interface for data sources."""

from abc import ABC, abstractmethod


class BaseDataSource(ABC):
    """데이터 소스 추상 인터페이스.

    모든 데이터 소스는 이 인터페이스를 구현해야 합니다.
    """

    @abstractmethod
    def fetch_data(self, key: str) -> dict | None:
        """데이터 조회.

        Args:
            key: 조회 키

        Returns:
            데이터 딕셔너리 또는 None
        """
        pass
```

### 예제: source_a.py (구현체)

```python
"""Source A implementation."""

from src.core.data.base import BaseDataSource
from src.utils.retry import with_retry


class SourceA(BaseDataSource):
    """소스 A 데이터 제공자."""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    @with_retry(max_attempts=3, wait_seconds=1.0)
    def fetch_data(self, key: str) -> dict | None:
        """소스 A에서 데이터 조회."""
        # 실제 API 호출 로직
        return {"source": "A", "key": key}
```

### 예제: aggregator.py (통합 로직)

```python
"""Multi-source data aggregator."""

from loguru import logger

from src.core.data.base import BaseDataSource


class DataAggregator:
    """여러 데이터 소스를 통합하는 aggregator.

    Args:
        source_a: 첫 번째 데이터 소스
        source_b: 두 번째 데이터 소스
    """

    def __init__(
        self,
        source_a: BaseDataSource,
        source_b: BaseDataSource,
    ) -> None:
        self.source_a = source_a
        self.source_b = source_b

    def get_combined_data(self, key: str) -> dict:
        """여러 소스에서 데이터를 가져와 통합.

        Args:
            key: 조회 키

        Returns:
            통합된 데이터
        """
        data_a = self.source_a.fetch_data(key)
        data_b = self.source_b.fetch_data(key)

        if not data_a or not data_b:
            logger.warning(f"{key}: 데이터 부족")
            return {}

        return {
            "key": key,
            "from_a": data_a,
            "from_b": data_b,
        }
```

## 2. 출력 렌더러 패턴

다양한 출력 형식(터미널, 파일, API 등)을 지원해야 할 때 사용하는 패턴입니다.

### 디렉토리 구조

```
src/core/output/
├── __init__.py
├── base.py              # ABC 인터페이스
├── terminal_renderer.py # 터미널 출력
├── csv_renderer.py      # CSV 파일 출력
└── json_renderer.py     # JSON 파일 출력
```

### 예제: terminal_renderer.py

```python
"""Terminal output using rich library."""

from rich.console import Console
from rich.table import Table


class TerminalRenderer:
    """Rich 라이브러리를 사용한 터미널 렌더러."""

    def __init__(self) -> None:
        self.console = Console()

    def display(self, results: list[dict]) -> None:
        """결과를 터미널에 표 형식으로 출력.

        Args:
            results: 출력할 결과 리스트
        """
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=4, justify="right")
        table.add_column("Name", width=20)
        table.add_column("Value", justify="right", width=10)

        for idx, result in enumerate(results, 1):
            table.add_row(
                str(idx),
                result.get("name", "Unknown"),
                str(result.get("value", 0)),
            )

        self.console.print(table)
```

## 3. 모델 패턴 (Pydantic)

데이터 구조를 명확히 정의하고 검증하는 패턴입니다.

### 예제: models.py

```python
"""Core data models."""

from pydantic import BaseModel, Field, computed_field


class DataItem(BaseModel):
    """데이터 아이템.

    Attributes:
        id: 고유 ID
        name: 이름
        value: 값
        metadata: 메타데이터
    """

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    value: float = Field(gt=0)
    metadata: dict = Field(default_factory=dict)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def display_name(self) -> str:
        """표시용 이름."""
        return f"{self.name} (ID: {self.id})"


class ProcessingResult(BaseModel):
    """처리 결과.

    Attributes:
        item: 데이터 아이템
        score: 점수
    """

    item: DataItem
    score: float = Field(ge=0, le=100)
```

## 4. 비즈니스 로직 엔진 패턴

핵심 처리 로직을 담당하는 엔진 패턴입니다.

### 예제: engine.py

```python
"""Core processing engine."""

from loguru import logger

from src.core.data.aggregator import DataAggregator
from src.core.models import DataItem, ProcessingResult
from src.utils.config import Settings


class ProcessingEngine:
    """데이터 처리 엔진.

    Args:
        config: 애플리케이션 설정
        aggregator: 데이터 aggregator
    """

    def __init__(
        self,
        config: Settings,
        aggregator: DataAggregator,
    ) -> None:
        self.config = config
        self.aggregator = aggregator

    def process(self, keys: list[str]) -> list[ProcessingResult]:
        """데이터 처리 실행.

        Args:
            keys: 처리할 키 리스트

        Returns:
            처리 결과 리스트
        """
        logger.info(f"처리 시작: {len(keys)}개 항목")

        results = []
        for key in keys:
            data = self.aggregator.get_combined_data(key)
            if not data:
                continue

            item = self._create_item(data)
            score = self._calculate_score(item)

            results.append(ProcessingResult(item=item, score=score))

        logger.info(f"처리 완료: {len(results)}개 결과")
        return results

    def _create_item(self, data: dict) -> DataItem:
        """데이터에서 아이템 생성."""
        # 구현 로직
        pass

    def _calculate_score(self, item: DataItem) -> float:
        """점수 계산."""
        # 구현 로직
        pass
```

## 5. batch_runner.py 통합 예제

JPPT의 `batch_runner.py`에서 위 패턴들을 통합하는 방법입니다.

```python
"""일회성 실행을 위한 배치 모드 실행기."""

from loguru import logger

from src.core.data.aggregator import DataAggregator
from src.core.data.source_a import SourceA
from src.core.data.source_b import SourceB
from src.core.engine import ProcessingEngine
from src.core.output.terminal_renderer import TerminalRenderer
from src.utils.config import Settings
from src.utils.telegram import TelegramNotifier


async def run_batch(settings: Settings) -> None:
    """배치 실행.

    Args:
        settings: 애플리케이션 설정
    """
    logger.info("Batch mode started")

    # Telegram notifier 초기화
    notifier = TelegramNotifier(
        bot_token=settings.telegram.bot_token,
        chat_id=settings.telegram.chat_id,
        enabled=settings.telegram.enabled,
    )

    await notifier.send_message(
        f"▶️ **{settings.app.name}** batch started"
    )

    try:
        # 1. 데이터 소스 초기화
        source_a = SourceA(api_key=settings.api_keys.source_a)
        source_b = SourceB(api_key=settings.api_keys.source_b)

        # 2. Aggregator 생성
        aggregator = DataAggregator(source_a=source_a, source_b=source_b)

        # 3. 엔진 생성
        engine = ProcessingEngine(
            config=settings,
            aggregator=aggregator,
        )

        # 4. 처리 실행
        keys = ["key1", "key2", "key3"]  # 실제로는 설정이나 API에서 가져옴
        results = engine.process(keys)

        # 5. 출력
        renderer = TerminalRenderer()
        renderer.display([r.model_dump() for r in results])

        # 6. Telegram 알림
        if settings.telegram.enabled:
            message = f"처리 완료: {len(results)}개 결과"
            await notifier.send_message(message)

        logger.info("Batch mode completed")
        await notifier.send_message(
            f"✅ **{settings.app.name}** batch completed"
        )

    except Exception as e:
        logger.error(f"처리 실패: {e}")
        await notifier.send_error(e, context="Batch mode failed")
        raise
```

## 실전 예제: KAVS 프로젝트

위 패턴들을 실제로 적용한 프로젝트는 [kavs](https://github.com/taein2301/kavs)를 참고하세요.

KAVS는 JPPT 템플릿을 기반으로 만든 코스닥 가치투자 종목 자동 선별 시스템입니다:

- **데이터 소스**: KRX, OpenDART API 통합
- **비즈니스 로직**: 가치투자 스크리닝 엔진
- **출력**: Rich 라이브러리를 사용한 터미널 테이블

### KAVS의 src/core/ 구조

```
src/core/
├── __init__.py
├── models.py            # Pydantic 모델 (Stock, ScreeningResult)
├── screener.py          # 스크리닝 엔진
├── data/                # 데이터 소스 패턴
│   ├── __init__.py
│   ├── base.py          # BaseDataSource ABC
│   ├── krx_source.py    # KRX 데이터 소스
│   ├── opendart_source.py  # OpenDART 데이터 소스
│   └── aggregator.py    # 멀티소스 통합
└── output/              # 출력 렌더러 패턴
    ├── __init__.py
    └── terminal_renderer.py  # Rich 터미널 출력
```

## 요약

1. **ABC 패턴**: 교체 가능한 컴포넌트 설계 (데이터 소스, 렌더러)
2. **Aggregator 패턴**: 여러 소스에서 데이터를 모아 통합
3. **Engine 패턴**: 핵심 비즈니스 로직을 담당
4. **Renderer 패턴**: 다양한 출력 형식 지원
5. **Pydantic 모델**: 타입 안전한 데이터 구조

이러한 패턴들은 JPPT의 `src/core/` 디렉토리에서 자유롭게 구현할 수 있으며, `src/utils/`의 인프라 유틸리티와 함께 사용하면 강력한 CLI 애플리케이션을 만들 수 있습니다.
