# Mini-Game Template

To add a new mini-game:

1. Copy this `_Template` folder and rename it to your game name
2. Create your game scripts under `Scripts/`
3. Create a new Scene under `Assets/Scenes/`
4. Add your game info to the `GameConfig` ScriptableObject:
   - GameId: unique snake_case identifier
   - DisplayName: shown in main menu
   - SceneName: matches your scene file name
   - Icon & Banner: UI assets
5. Implement your game manager extending MonoBehaviour
6. Use shared systems:
   - `CurrencyManager.Instance` for coins/gems
   - `AudioManager.Instance` for sounds
   - `SaveManager.Instance.Data.GetGameProgress(gameId)` for save data
   - `GameEvents.FireLevelCompleted(stars)` when level is done
   - `GameManager.Instance.LoadMainMenu()` to return to menu

## Folder Structure
```
YourGame/
├── Scripts/
│   ├── YourGameManager.cs
│   └── ... other scripts
├── Prefabs/
└── Levels/  (optional)
```
