using UnityEngine;
using UnityEngine.UI;
using TMPro;
using SuperGameApp.Core.Managers;
using SuperGameApp.Core.Events;

namespace SuperGameApp.MiniGames.WaterSort
{
    /// <summary>
    /// UI controller for the Water Sort game scene.
    /// </summary>
    public class WaterSortUI : MonoBehaviour
    {
        [Header("Top Bar")]
        [SerializeField] private TextMeshProUGUI _levelText;
        [SerializeField] private TextMeshProUGUI _movesText;
        [SerializeField] private TextMeshProUGUI _coinsText;
        [SerializeField] private Button _backButton;

        [Header("Action Buttons")]
        [SerializeField] private Button _undoButton;
        [SerializeField] private Button _restartButton;
        [SerializeField] private Button _hintButton;

        [Header("Popups")]
        [SerializeField] private GameObject _levelCompletePopup;
        [SerializeField] private GameObject _pausePopup;
        [SerializeField] private TextMeshProUGUI _completeStarsText;
        [SerializeField] private TextMeshProUGUI _completeCoinsText;
        [SerializeField] private Button _nextLevelButton;
        [SerializeField] private Button _replayButton;
        [SerializeField] private Button _doubleRewardButton;

        private void Start()
        {
            _backButton.onClick.AddListener(OnBackClicked);
            _undoButton.onClick.AddListener(OnUndoClicked);
            _restartButton.onClick.AddListener(OnRestartClicked);
            _hintButton.onClick.AddListener(OnHintClicked);

            if (_nextLevelButton != null)
                _nextLevelButton.onClick.AddListener(OnNextLevel);
            if (_replayButton != null)
                _replayButton.onClick.AddListener(OnReplay);
            if (_doubleRewardButton != null)
                _doubleRewardButton.onClick.AddListener(OnDoubleReward);

            _levelCompletePopup.SetActive(false);
            UpdateCoinsDisplay();
        }

        private void OnEnable()
        {
            GameEvents.OnCoinsChanged += _ => UpdateCoinsDisplay();
        }

        private void OnDisable()
        {
            GameEvents.OnCoinsChanged -= _ => UpdateCoinsDisplay();
        }

        public void UpdateLevel(int level) => _levelText.text = $"Level {level}";
        public void UpdateMoves(int moves) => _movesText.text = $"Moves: {moves}";
        private void UpdateCoinsDisplay() => _coinsText.text = CurrencyManager.Instance.Coins.ToString();

        public void ShowLevelComplete(int stars, int coinReward)
        {
            _levelCompletePopup.SetActive(true);
            _completeStarsText.text = new string('*', stars);  // Replace with star icons in production
            _completeCoinsText.text = $"+{coinReward}";
        }

        private void OnBackClicked()
        {
            AudioManager.Instance.PlayButtonClick();
            GameManager.Instance.LoadMainMenu();
        }

        private void OnUndoClicked()
        {
            AudioManager.Instance.PlayButtonClick();
            WaterSortGameManager.Instance.UndoMove();
        }

        private void OnRestartClicked()
        {
            AudioManager.Instance.PlayButtonClick();
            WaterSortGameManager.Instance.RestartLevel();
        }

        private void OnHintClicked()
        {
            AudioManager.Instance.PlayButtonClick();
            // Show rewarded ad for hint
            AdsManager.Instance.ShowRewarded(() =>
            {
                // TODO: Implement hint logic - highlight the best move
                Debug.Log("[WaterSort] Hint used after rewarded ad");
            });
        }

        private void OnNextLevel()
        {
            _levelCompletePopup.SetActive(false);
            WaterSortGameManager.Instance.LoadNextLevel();
        }

        private void OnReplay()
        {
            _levelCompletePopup.SetActive(false);
            WaterSortGameManager.Instance.RestartLevel();
        }

        private void OnDoubleReward()
        {
            AdsManager.Instance.ShowRewarded(() =>
            {
                int bonus = GameManager.Instance.Config.Ads.RewardedAdCoinBonus;
                CurrencyManager.Instance.AddCoins(bonus);
                _doubleRewardButton.interactable = false;
            });
        }
    }
}
