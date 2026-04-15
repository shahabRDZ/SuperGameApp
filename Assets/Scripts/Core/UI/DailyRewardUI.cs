using System;
using UnityEngine;
using UnityEngine.UI;
using TMPro;
using SuperGameApp.Core.Managers;
using SuperGameApp.Core.Events;

namespace SuperGameApp.Core.UI
{
    /// <summary>
    /// 7-day daily reward system with escalating rewards.
    /// </summary>
    public class DailyRewardUI : MonoBehaviour
    {
        [SerializeField] private Transform _daysContainer;
        [SerializeField] private GameObject _dayItemPrefab;
        [SerializeField] private Button _claimButton;
        [SerializeField] private Button _closeButton;
        [SerializeField] private TextMeshProUGUI _rewardText;

        private int _currentDay;
        private bool _canClaim;

        private void OnEnable()
        {
            var data = SaveManager.Instance.Data;
            var config = GameManager.Instance.Config.DailyRewards;

            _currentDay = data.DailyRewardDay % config.CoinRewards.Length;
            _canClaim = CanClaimToday(data.LastDailyRewardDate);

            RefreshDayDisplay(config);

            _claimButton.interactable = _canClaim;
            _claimButton.onClick.AddListener(ClaimReward);
            _closeButton.onClick.AddListener(Close);

            if (_canClaim)
            {
                int coins = config.CoinRewards[_currentDay];
                int gems = config.GemRewards[_currentDay];
                string text = $"+{coins} coins";
                if (gems > 0) text += $" +{gems} gems";
                _rewardText.text = text;
            }
            else
            {
                _rewardText.text = "Come back tomorrow!";
            }
        }

        private void OnDisable()
        {
            _claimButton.onClick.RemoveListener(ClaimReward);
            _closeButton.onClick.RemoveListener(Close);
        }

        private bool CanClaimToday(string lastDate)
        {
            if (string.IsNullOrEmpty(lastDate)) return true;

            if (DateTime.TryParse(lastDate, out DateTime last))
                return DateTime.UtcNow.Date > last.Date;

            return true;
        }

        private void ClaimReward()
        {
            if (!_canClaim) return;

            var config = GameManager.Instance.Config.DailyRewards;
            int coins = config.CoinRewards[_currentDay];
            int gems = config.GemRewards[_currentDay];

            CurrencyManager.Instance.AddCoins(coins);
            if (gems > 0) CurrencyManager.Instance.AddGems(gems);

            var data = SaveManager.Instance.Data;
            data.DailyRewardDay++;
            data.LastDailyRewardDate = DateTime.UtcNow.ToString("o");
            SaveManager.Instance.Save();

            AudioManager.Instance.PlayCoinCollect();
            GameEvents.FireDailyRewardClaimed();

            _canClaim = false;
            _claimButton.interactable = false;
            _rewardText.text = "Claimed! See you tomorrow!";
        }

        private void RefreshDayDisplay(Data.DailyRewardConfig config)
        {
            foreach (Transform child in _daysContainer)
                Destroy(child.gameObject);

            for (int i = 0; i < config.CoinRewards.Length; i++)
            {
                var item = Instantiate(_dayItemPrefab, _daysContainer);
                var text = item.GetComponentInChildren<TextMeshProUGUI>();
                if (text != null)
                {
                    text.text = $"Day {i + 1}\n{config.CoinRewards[i]}";
                }

                var image = item.GetComponent<Image>();
                if (image != null)
                {
                    if (i < _currentDay) image.color = Color.gray;       // Already claimed
                    else if (i == _currentDay) image.color = Color.yellow; // Today
                    else image.color = Color.white;                        // Upcoming
                }
            }
        }

        private void Close()
        {
            AudioManager.Instance.PlayButtonClick();
            UIManager.Instance.HidePanel(gameObject);
        }
    }
}
