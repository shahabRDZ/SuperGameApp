# Super Game App - Architecture Document

## Tech Stack
- **Engine**: Unity 2022.3 LTS (C#)
- **Target**: Android & iOS
- **Backend**: Firebase (Auth, Firestore, Remote Config)
- **Ads**: Unity Ads + AdMob Mediation
- **Analytics**: Firebase Analytics

## Architecture Pattern: Modular Service-Oriented

```
SuperGameApp/
├── Assets/
│   ├── Scripts/
│   │   ├── Core/                    # Shared systems
│   │   │   ├── Managers/            # Singleton managers
│   │   │   │   ├── GameManager.cs
│   │   │   │   ├── AudioManager.cs
│   │   │   │   ├── CurrencyManager.cs
│   │   │   │   ├── AdsManager.cs
│   │   │   │   ├── SaveManager.cs
│   │   │   │   └── UIManager.cs
│   │   │   ├── Data/                # Data models & ScriptableObjects
│   │   │   │   ├── PlayerData.cs
│   │   │   │   ├── GameConfig.cs
│   │   │   │   └── CurrencyData.cs
│   │   │   ├── UI/                  # Shared UI components
│   │   │   │   ├── MainMenuController.cs
│   │   │   │   ├── GameCardUI.cs
│   │   │   │   ├── ProfileUI.cs
│   │   │   │   ├── SettingsUI.cs
│   │   │   │   └── DailyRewardUI.cs
│   │   │   ├── Utils/               # Helpers
│   │   │   │   └── Singleton.cs
│   │   │   └── Events/              # Event system
│   │   │       └── GameEvents.cs
│   │   │
│   │   └── MiniGames/               # Each game is a module
│   │       ├── WaterSort/
│   │       │   ├── Scripts/
│   │       │   │   ├── WaterSortGameManager.cs
│   │       │   │   ├── Tube.cs
│   │       │   │   ├── LiquidLayer.cs
│   │       │   │   ├── PourAnimation.cs
│   │       │   │   ├── LevelGenerator.cs
│   │       │   │   └── WaterSortUI.cs
│   │       │   ├── Prefabs/
│   │       │   └── Levels/
│   │       │       └── LevelDatabase.cs
│   │       │
│   │       └── _Template/           # Template for new mini-games
│   │           └── README.md
│   │
│   ├── Scenes/
│   │   ├── BootScene.unity
│   │   ├── MainMenuScene.unity
│   │   └── WaterSortScene.unity
│   │
│   └── UI/
│       ├── Prefabs/
│       └── Sprites/
│
└── Docs/
    └── ARCHITECTURE.md
```

## Design Principles
1. **SOLID** - Each class has single responsibility
2. **Modular** - Mini-games are self-contained modules
3. **Event-Driven** - Decoupled communication via events
4. **Data-Driven** - Levels and configs via ScriptableObjects
5. **DI-Light** - Manager singletons accessed via ServiceLocator pattern

## Adding a New Mini-Game
1. Create folder under `MiniGames/`
2. Implement `IMiniGame` interface
3. Create a new Scene
4. Register in `GameConfig` ScriptableObject
5. Add card to main menu grid

## Navigation Flow
```
Boot → Main Menu → Game Selection → [Mini-Game Scene] → Results → Main Menu
                 → Profile
                 → Settings
                 → Daily Rewards
                 → Shop
```

## Monetization Points
- Rewarded ad: Extra coins, undo moves, hints
- Interstitial: Between levels (every 3rd level)
- IAP: Remove ads, coin packs, premium themes
- Daily rewards: 7-day cycle with increasing rewards
