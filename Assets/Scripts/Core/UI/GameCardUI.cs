using UnityEngine;
using UnityEngine.UI;
using TMPro;
using SuperGameApp.Core.Data;
using SuperGameApp.Core.Events;
using SuperGameApp.Core.Managers;

namespace SuperGameApp.Core.UI
{
    /// <summary>
    /// Individual game card in the main menu grid.
    /// </summary>
    public class GameCardUI : MonoBehaviour
    {
        [SerializeField] private Image _iconImage;
        [SerializeField] private Image _bannerImage;
        [SerializeField] private Image _backgroundImage;
        [SerializeField] private TextMeshProUGUI _titleText;
        [SerializeField] private TextMeshProUGUI _progressText;
        [SerializeField] private GameObject _lockOverlay;
        [SerializeField] private TextMeshProUGUI _unlockCostText;
        [SerializeField] private Button _playButton;

        private MiniGameInfo _gameInfo;

        public void Setup(MiniGameInfo gameInfo, GameProgress progress)
        {
            _gameInfo = gameInfo;

            _titleText.text = gameInfo.DisplayName;
            _iconImage.sprite = gameInfo.Icon;
            _backgroundImage.color = gameInfo.ThemeColor;

            if (gameInfo.Banner != null)
                _bannerImage.sprite = gameInfo.Banner;

            bool isLocked = gameInfo.IsLocked && progress.HighestLevel == 0;
            _lockOverlay.SetActive(isLocked);

            if (isLocked && gameInfo.UnlockCost > 0)
                _unlockCostText.text = gameInfo.UnlockCost.ToString();

            if (progress.HighestLevel > 0)
                _progressText.text = $"Level {progress.HighestLevel}";
            else
                _progressText.text = "New!";

            _playButton.onClick.AddListener(OnPlayClicked);
        }

        private void OnPlayClicked()
        {
            AudioManager.Instance.PlayButtonClick();

            if (_gameInfo.IsLocked)
            {
                if (CurrencyManager.Instance.SpendCoins(_gameInfo.UnlockCost))
                {
                    _lockOverlay.SetActive(false);
                    GameEvents.FireMiniGameSelected(_gameInfo.GameId);
                }
            }
            else
            {
                GameEvents.FireMiniGameSelected(_gameInfo.GameId);
            }
        }
    }
}
