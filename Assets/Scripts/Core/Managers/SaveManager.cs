using UnityEngine;
using SuperGameApp.Core.Data;
using SuperGameApp.Core.Utils;

namespace SuperGameApp.Core.Managers
{
    /// <summary>
    /// Handles serialization of PlayerData to persistent storage.
    /// Uses PlayerPrefs for simplicity; can be swapped to file-based or cloud save.
    /// </summary>
    public class SaveManager : Singleton<SaveManager>
    {
        private const string SAVE_KEY = "PlayerData";
        private PlayerData _cachedData;

        public PlayerData Data
        {
            get
            {
                if (_cachedData == null)
                    Load();
                return _cachedData;
            }
        }

        public void Save()
        {
            string json = JsonUtility.ToJson(_cachedData);
            PlayerPrefs.SetString(SAVE_KEY, json);
            PlayerPrefs.Save();
        }

        public void Load()
        {
            if (PlayerPrefs.HasKey(SAVE_KEY))
            {
                string json = PlayerPrefs.GetString(SAVE_KEY);
                _cachedData = JsonUtility.FromJson<PlayerData>(json);
            }
            else
            {
                _cachedData = new PlayerData();
                Save();
            }
        }

        public void ResetData()
        {
            _cachedData = new PlayerData();
            Save();
        }

        private void OnApplicationPause(bool pause)
        {
            if (pause) Save();
        }

        private void OnApplicationQuit()
        {
            Save();
            base.OnApplicationQuit();
        }
    }
}
