using SuperGameApp.Core.Data;
using SuperGameApp.Core.Events;
using SuperGameApp.Core.Utils;

namespace SuperGameApp.Core.Managers
{
    /// <summary>
    /// Manages coins and gems. All currency changes go through here.
    /// </summary>
    public class CurrencyManager : Singleton<CurrencyManager>
    {
        public int Coins => SaveManager.Instance.Data.Coins;
        public int Gems => SaveManager.Instance.Data.Gems;

        public void AddCoins(int amount)
        {
            SaveManager.Instance.Data.Coins += amount;
            SaveManager.Instance.Save();
            GameEvents.FireCoinsChanged(Coins);
        }

        public bool SpendCoins(int amount)
        {
            if (Coins < amount) return false;

            SaveManager.Instance.Data.Coins -= amount;
            SaveManager.Instance.Save();
            GameEvents.FireCoinsChanged(Coins);
            return true;
        }

        public void AddGems(int amount)
        {
            SaveManager.Instance.Data.Gems += amount;
            SaveManager.Instance.Save();
            GameEvents.FireGemsChanged(Gems);
        }

        public bool SpendGems(int amount)
        {
            if (Gems < amount) return false;

            SaveManager.Instance.Data.Gems -= amount;
            SaveManager.Instance.Save();
            GameEvents.FireGemsChanged(Gems);
            return true;
        }
    }
}
