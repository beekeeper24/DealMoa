from dataclasses import dataclass


@dataclass(frozen=True)
class DemoDeal:
    title: str
    source_url: str
    seller: str
    original_price: int
    sale_price: int
    favorite_user_keys: tuple[str, ...]


@dataclass(frozen=True)
class DemoAuctionBid:
    user_key: str
    amount: int


@dataclass(frozen=True)
class DemoAuction:
    title: str
    source_url: str
    seller: str
    current_price: int
    bid_count: int
    favorite_user_keys: tuple[str, ...]
    bids: tuple[DemoAuctionBid, ...]


@dataclass(frozen=True)
class DemoProduct:
    name: str
    brand: str
    model_name: str
    category: str
    specs: dict[str, object]
    deal: DemoDeal
    auction: DemoAuction


DEMO_USER_KEYS = (
    "demo-user-01",
    "demo-user-02",
    "demo-user-03",
    "demo-user-04",
)


KOREAN_DEMO_PRODUCTS: tuple[DemoProduct, ...] = (
    DemoProduct(
        name="삼성 갤럭시 S26 256GB",
        brand="삼성전자",
        model_name="SM-S260N-256",
        category="스마트폰",
        specs={
            "설명": "사진과 게임 성능을 중시하는 사용자를 위한 플래그십 스마트폰",
            "화면": "6.8인치 AMOLED",
            "저장공간": "256GB",
            "색상": ["문라이트 실버", "코발트 블루"],
            "검색메모": "한국어 검색 갤럭시 스마트폰 플래그십",
        },
        deal=DemoDeal(
            title="삼성 갤럭시 S26 256GB 자급제 출시 특가",
            source_url="https://demo.dealmoa.local/deals/galaxy-s26-256",
            seller="딜모아 전자관",
            original_price=1_390_000,
            sale_price=1_090_000,
            favorite_user_keys=("demo-user-01", "demo-user-02", "demo-user-03"),
        ),
        auction=DemoAuction(
            title="갤럭시 S26 256GB 미개봉 경매",
            source_url="https://demo.dealmoa.local/auctions/galaxy-s26-256",
            seller="딜모아 경매관",
            current_price=950_000,
            bid_count=3,
            favorite_user_keys=("demo-user-01", "demo-user-02"),
            bids=(
                DemoAuctionBid("demo-user-01", 900_000),
                DemoAuctionBid("demo-user-02", 925_000),
                DemoAuctionBid("demo-user-03", 950_000),
            ),
        ),
    ),
    DemoProduct(
        name="LG 스탠바이미 고 27인치",
        brand="LG전자",
        model_name="27LX5QKNA",
        category="생활가전",
        specs={
            "설명": "캠핑과 거실을 오가며 쓰기 좋은 이동식 터치 TV",
            "화면": "27인치 터치 디스플레이",
            "배터리": "내장형",
            "활용": ["캠핑", "거실", "침실"],
            "검색메모": "한국어 검색 이동식 TV 스탠바이미",
        },
        deal=DemoDeal(
            title="LG 스탠바이미 고 캠핑 시즌 핫딜",
            source_url="https://demo.dealmoa.local/deals/lg-standbyme-go",
            seller="리빙가전 특가몰",
            original_price=1_190_000,
            sale_price=899_000,
            favorite_user_keys=("demo-user-01", "demo-user-04"),
        ),
        auction=DemoAuction(
            title="LG 스탠바이미 고 전시품 경매",
            source_url="https://demo.dealmoa.local/auctions/lg-standbyme-go",
            seller="리퍼브 경매센터",
            current_price=640_000,
            bid_count=2,
            favorite_user_keys=("demo-user-02",),
            bids=(
                DemoAuctionBid("demo-user-02", 610_000),
                DemoAuctionBid("demo-user-04", 640_000),
            ),
        ),
    ),
    DemoProduct(
        name="애플 맥북 에어 13 M4",
        brand="Apple",
        model_name="MW123KH/A",
        category="노트북",
        specs={
            "설명": "가벼운 휴대성과 긴 배터리를 원하는 업무용 노트북",
            "칩셋": "Apple M4",
            "메모리": "16GB",
            "저장공간": "512GB",
            "검색메모": "한국어 검색 맥북 노트북 대학생 업무용",
        },
        deal=DemoDeal(
            title="맥북 에어 13 M4 교육 할인급 특가",
            source_url="https://demo.dealmoa.local/deals/macbook-air-m4-13",
            seller="프리미엄 디지털",
            original_price=1_890_000,
            sale_price=1_590_000,
            favorite_user_keys=("demo-user-01", "demo-user-02", "demo-user-04"),
        ),
        auction=DemoAuction(
            title="맥북 에어 M4 실버 미개봉 경매",
            source_url="https://demo.dealmoa.local/auctions/macbook-air-m4-13",
            seller="디지털 경매마켓",
            current_price=1_420_000,
            bid_count=3,
            favorite_user_keys=("demo-user-01", "demo-user-03"),
            bids=(
                DemoAuctionBid("demo-user-01", 1_360_000),
                DemoAuctionBid("demo-user-03", 1_390_000),
                DemoAuctionBid("demo-user-04", 1_420_000),
            ),
        ),
    ),
    DemoProduct(
        name="소니 WH-1000XM6 노이즈캔슬링 헤드폰",
        brand="Sony",
        model_name="WH-1000XM6",
        category="음향기기",
        specs={
            "설명": "출퇴근과 집중 작업에 어울리는 무선 노이즈캔슬링 헤드폰",
            "기능": ["노이즈캔슬링", "블루투스", "고해상도 오디오"],
            "색상": "블랙",
            "검색메모": "한국어 검색 헤드폰 무선 음향기기",
        },
        deal=DemoDeal(
            title="소니 WH-1000XM6 노이즈캔슬링 헤드폰 특가",
            source_url="https://demo.dealmoa.local/deals/sony-wh-1000xm6",
            seller="사운드딜",
            original_price=499_000,
            sale_price=399_000,
            favorite_user_keys=("demo-user-02", "demo-user-03"),
        ),
        auction=DemoAuction(
            title="소니 WH-1000XM6 블랙 단순개봉 경매",
            source_url="https://demo.dealmoa.local/auctions/sony-wh-1000xm6",
            seller="오디오 리퍼브",
            current_price=322_000,
            bid_count=2,
            favorite_user_keys=("demo-user-03",),
            bids=(
                DemoAuctionBid("demo-user-02", 300_000),
                DemoAuctionBid("demo-user-03", 322_000),
            ),
        ),
    ),
    DemoProduct(
        name="다이슨 슈퍼소닉 뉴럴 헤어드라이어",
        brand="Dyson",
        model_name="HD16-KR",
        category="생활가전",
        specs={
            "설명": "선물용으로 인기 있는 프리미엄 헤어드라이어",
            "기능": ["두피 보호", "온도 제어", "빠른 건조"],
            "색상": "세라믹 핑크",
            "검색메모": "한국어 검색 드라이어 미용가전 선물",
        },
        deal=DemoDeal(
            title="다이슨 슈퍼소닉 뉴럴 선물 시즌 핫딜",
            source_url="https://demo.dealmoa.local/deals/dyson-supersonic-neural",
            seller="뷰티가전 스토어",
            original_price=599_000,
            sale_price=489_000,
            favorite_user_keys=("demo-user-01", "demo-user-03"),
        ),
        auction=DemoAuction(
            title="다이슨 슈퍼소닉 뉴럴 미사용품 경매",
            source_url="https://demo.dealmoa.local/auctions/dyson-supersonic-neural",
            seller="프리미엄 리셀",
            current_price=410_000,
            bid_count=2,
            favorite_user_keys=("demo-user-01",),
            bids=(
                DemoAuctionBid("demo-user-01", 390_000),
                DemoAuctionBid("demo-user-04", 410_000),
            ),
        ),
    ),
    DemoProduct(
        name="닌텐도 스위치 2 마리오 번들",
        brand="Nintendo",
        model_name="NSW2-MARIO-KR",
        category="게임기",
        specs={
            "설명": "가족과 함께 즐기기 좋은 국내 정발 콘솔 게임기 번들",
            "구성": ["본체", "마리오 번들", "조이콘"],
            "정발": "국내 정식 발매",
            "검색메모": "한국어 검색 게임기 콘솔 가족 선물",
        },
        deal=DemoDeal(
            title="닌텐도 스위치 2 마리오 번들 예약 특가",
            source_url="https://demo.dealmoa.local/deals/nintendo-switch2-mario",
            seller="게임핫딜",
            original_price=598_000,
            sale_price=548_000,
            favorite_user_keys=("demo-user-02", "demo-user-03", "demo-user-04"),
        ),
        auction=DemoAuction(
            title="닌텐도 스위치 2 마리오 번들 미개봉 경매",
            source_url="https://demo.dealmoa.local/auctions/nintendo-switch2-mario",
            seller="콘솔 경매장",
            current_price=610_000,
            bid_count=3,
            favorite_user_keys=("demo-user-02", "demo-user-04"),
            bids=(
                DemoAuctionBid("demo-user-02", 570_000),
                DemoAuctionBid("demo-user-03", 590_000),
                DemoAuctionBid("demo-user-04", 610_000),
            ),
        ),
    ),
)
