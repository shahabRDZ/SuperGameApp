using UnityEngine;
using UnityEngine.SceneManagement;
using SuperGameApp.Core.Data;
using SuperGameApp.Core.Events;
using SuperGameApp.Core.Utils;

namespace SuperGameApp.Core.Managers
{
    /// <summary>
    /// Top-level manager controlling app flow, scene transitions, and game state.
    /// </summary>
    public class GameManager : Singleton<GameManager>
    {
        [SerializeField] private GameConfig _gameConfig;

        public GameConfig Config => _gameConfig;
        public string CurrentGameId { get; private set; }

        private int _levelsPlayedSinceLastAd;

        protected override void Awake()
        {
            base.Awake();
            Application.targetFrameRate = 60;
            Screen.sleepTimeout = SleepTimeout.NeverSleep;
        }

        private void OnEnable()
        {
            GameEvents.OnLevelCompleted += HandleLevelCompleted;
            GameEvents.OnMiniGameSelected += HandleGameSelected;
        }

        private void OnDisable()
        {
            GameEvents.OnLevelCompleted -= HandleLevelCompleted;
            GameEvents.OnMiniGameSelected -= HandleGameSelected;
        }

        public void LoadMainMenu()
        {
            CurrentGameId = null;
            SceneManager.LoadScene("MainMenuScene");
        }

        public void LoadMiniGame(string gameId)
        {
            var gameInfo = _gameConfig.MiniGames.Find(g => g.GameId == gameId);
            if (gameInfo == null)
            {
                Debug.LogError($"Mini-game not found: {gameId}");
                return;
            }

            CurrentGameId = gameId;
            SceneManager.LoadScene(gameInfo.SceneName);
        }

        private void HandleGameSelected(string gameId)
        {
            LoadMiniGame(gameId);
        }

        private void HandleLevelCompleted(int stars)
        {
            _levelsPlayedSinceLastAd++;

            int coinReward = stars * 10;
            CurrencyManager.Instance.AddCoins(coinReward);

            if (ShouldShowInterstitial())
            {
                AdsManager.Instance.ShowInterstitial();
                _levelsPlayedSinceLastAd = 0;
            }
        }

        private bool ShouldShowInterstitial()
        {
            if (SaveManager.Instance.Data.AdsRemoved) return false;
            return _levelsPlayedSinceLastAd >= _gameConfig.Ads.InterstitialFrequency;
        }

        public MiniGameInfo GetGameInfo(string gameId)
        {
            return _gameConfig.MiniGames.Find(g => g.GameId == gameId);
        }
    }
}
