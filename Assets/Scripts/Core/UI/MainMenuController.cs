using UnityEngine;
using UnityEngine.UI;
using TMPro;
using SuperGameApp.Core.Managers;
using SuperGameApp.Core.Events;

namespace SuperGameApp.Core.UI
{
    /// <summary>
    /// Controls the main menu dashboard with game cards grid.
    /// </summary>
    public class MainMenuController : MonoBehaviour
    {
        [Header("UI References")]
        [SerializeField] private Transform _gameCardsContainer;
        [SerializeField] private GameObject _gameCardPrefab;
        [SerializeField] private TextMeshProUGUI _coinsText;
        [SerializeField] private TextMeshProUGUI _gemsText;
        [SerializeField] private TextMeshProUGUI _usernameText;
        [SerializeField] private Button _profileButton;
        [SerializeField] private Button _settingsButton;
        [SerializeField] private Button _dailyRewardButton;

        [Header("Panels")]
        [SerializeField] private GameObject _profilePanel;
        [SerializeField] private GameObject _settingsPanel;
        [SerializeField] private GameObject _dailyRewardPanel;

        private void Start()
        {
            RefreshUI();
            PopulateGameCards();
            SetupButtons();
        }

        private void OnEnable()
        {
            GameEvents.OnCoinsChanged += UpdateCoins;
            GameEvents.OnGemsChanged += UpdateGems;
        }

        private void OnDisable()
        {
            GameEvents.OnCoinsChanged -= UpdateCoins;
            GameEvents.OnGemsChanged -= UpdateGems;
        }

        private void RefreshUI()
        {
            var data = SaveManager.Instance.Data;
            _coinsText.text = FormatNumber(data.Coins);
            _gemsText.text = FormatNumber(data.Gems);
            _usernameText.text = data.Username;
        }

        private void PopulateGameCards()
        {
            var config = GameManager.Instance.Config;
            foreach (var game in config.MiniGames)
            {
                var cardObj = Instantiate(_gameCardPrefab, _gameCardsContainer);
                var card = cardObj.GetComponent<GameCardUI>();
                if (card != null)
                {
                    var progress = SaveManager.Instance.Data.GetGameProgress(game.GameId);
                    card.Setup(game, progress);
                }
            }
        }

        private void SetupButtons()
        {
            _profileButton.onClick.AddListener(() => UIManager.Instance.ShowPanel(_profilePanel));
            _settingsButton.onClick.AddListener(() => UIManager.Instance.ShowPanel(_settingsPanel));
            _dailyRewardButton.onClick.AddListener(() => UIManager.Instance.ShowPanel(_dailyRewardPanel));
        }

        private void UpdateCoins(int amount) => _coinsText.text = FormatNumber(amount);
        private void UpdateGems(int amount) => _gemsText.text = FormatNumber(amount);

        private string FormatNumber(int num)
        {
            if (num >= 1000000) return $"{num / 1000000f:F1}M";
            if (num >= 1000) return $"{num / 1000f:F1}K";
            return num.ToString();
        }
    }
}
