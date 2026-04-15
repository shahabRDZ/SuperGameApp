using System.Collections.Generic;
using UnityEngine;
using SuperGameApp.Core.Managers;
using SuperGameApp.Core.Events;
using SuperGameApp.Core.Data;

namespace SuperGameApp.MiniGames.WaterSort
{
    /// <summary>
    /// Core game manager for the Water Sort Puzzle mini-game.
    /// Handles game state, move validation, undo system, and win detection.
    /// </summary>
    public class WaterSortGameManager : MonoBehaviour
    {
        public static WaterSortGameManager Instance { get; private set; }

        [Header("References")]
        [SerializeField] private Transform _tubeContainer;
        [SerializeField] private GameObject _tubePrefab;
        [SerializeField] private PourAnimation _pourAnimation;
        [SerializeField] private WaterSortUI _ui;
        [SerializeField] private LevelDatabase _levelDatabase;

        [Header("Colors")]
        [SerializeField] private Color[] _liquidColors = new Color[]
        {
            Color.red,
            Color.blue,
            Color.green,
            Color.yellow,
            new Color(1f, 0.5f, 0f),    // Orange
            new Color(0.5f, 0f, 1f),    // Purple
            new Color(0f, 1f, 1f),      // Cyan
            new Color(1f, 0.4f, 0.7f),  // Pink
            new Color(0.6f, 0.3f, 0f),  // Brown
            new Color(0.5f, 0.5f, 0.5f) // Gray
        };

        [Header("Layout")]
        [SerializeField] private float _tubeSpacing = 1.5f;
        [SerializeField] private int _maxTubesPerRow = 5;

        private List<Tube> _tubes = new List<Tube>();
        private Tube _selectedTube;
        private int _currentLevel;
        private int _moveCount;
        private int _layersPerTube = 4;

        // Undo system
        private Stack<MoveRecord> _undoStack = new Stack<MoveRecord>();

        private struct MoveRecord
        {
            public int FromTube;
            public int ToTube;
            public int[] MovedLayers;
        }

        private void Awake()
        {
            if (Instance == null) Instance = this;
            else Destroy(gameObject);
        }

        private void Start()
        {
            var progress = SaveManager.Instance.Data.GetGameProgress("water_sort");
            _currentLevel = progress.HighestLevel + 1;
            if (_currentLevel < 1) _currentLevel = 1;

            LoadLevel(_currentLevel);
        }

        public Color GetColor(int colorIndex)
        {
            if (colorIndex <= 0 || colorIndex > _liquidColors.Length)
                return Color.clear;
            return _liquidColors[colorIndex - 1];
        }

        public void LoadLevel(int levelNumber)
        {
            _currentLevel = levelNumber;
            _moveCount = 0;
            _undoStack.Clear();
            _selectedTube = null;

            ClearTubes();

            WaterSortLevel level;

            // Use database levels if available, otherwise generate
            if (_levelDatabase != null && levelNumber <= _levelDatabase.Levels.Count)
            {
                level = _levelDatabase.Levels[levelNumber - 1];
            }
            else
            {
                var (colors, empties, shuffles) = LevelGenerator.GetDifficultyForLevel(levelNumber);
                level = LevelGenerator.Generate(levelNumber, colors, empties, 4, shuffles);
            }

            _layersPerTube = level.LayersPerTube;
            CreateTubes(level);

            _ui.UpdateLevel(levelNumber);
            _ui.UpdateMoves(0);
        }

        public void LoadNextLevel()
        {
            LoadLevel(_currentLevel + 1);
        }

        public void RestartLevel()
        {
            LoadLevel(_currentLevel);
            GameEvents.FireLevelRestarted();
        }

        public void OnTubeClicked(Tube tube)
        {
            if (_pourAnimation != null && _pourAnimation.IsAnimating) return;

            if (_selectedTube == null)
            {
                if (tube.IsEmpty) return;
                if (tube.IsComplete) return;

                _selectedTube = tube;
                tube.SetSelected(true);
                AudioManager.Instance.PlayButtonClick();
            }
            else if (_selectedTube == tube)
            {
                // Deselect
                _selectedTube.SetSelected(false);
                _selectedTube = null;
                AudioManager.Instance.PlayButtonClick();
            }
            else
            {
                // Attempt pour
                TryPour(_selectedTube, tube);
            }
        }

        private void TryPour(Tube source, Tube target)
        {
            int topColor = source.TopColor;
            int topCount = source.TopColorCount();

            if (!target.CanReceive(topColor, 1))
            {
                // Invalid move - deselect and select the new tube instead
                source.SetSelected(false);

                if (!target.IsEmpty && !target.IsComplete)
                {
                    _selectedTube = target;
                    target.SetSelected(true);
                }
                else
                {
                    _selectedTube = null;
                }
                return;
            }

            // Calculate how many layers can actually move
            int spaceInTarget = _layersPerTube - target.LayerCount;
            int layersToMove = Mathf.Min(topCount, spaceInTarget);

            source.SetSelected(false);
            _selectedTube = null;

            if (_pourAnimation != null)
            {
                StartCoroutine(_pourAnimation.AnimatePour(source, target, () =>
                {
                    ExecutePour(source, target);
                }));
            }
            else
            {
                ExecutePour(source, target);
            }
        }

        private void ExecutePour(Tube source, Tube target)
        {
            int[] removed = source.RemoveTopLayers();

            // Only add layers that fit
            int space = _layersPerTube - target.LayerCount;
            int toAdd = Mathf.Min(removed.Length, space);
            int[] layersToAdd = new int[toAdd];
            System.Array.Copy(removed, 0, layersToAdd, 0, toAdd);

            // Put back excess layers
            if (toAdd < removed.Length)
            {
                int[] excess = new int[removed.Length - toAdd];
                System.Array.Copy(removed, toAdd, excess, 0, excess.Length);
                source.AddLayers(excess);
            }

            target.AddLayers(layersToAdd);

            // Record for undo
            _undoStack.Push(new MoveRecord
            {
                FromTube = source.TubeIndex,
                ToTube = target.TubeIndex,
                MovedLayers = layersToAdd
            });

            _moveCount++;
            _ui.UpdateMoves(_moveCount);

            CheckWinCondition();
        }

        public void UndoMove()
        {
            if (_undoStack.Count == 0) return;

            // First undo is free, subsequent ones cost coins or watch ad
            if (_undoStack.Count > 0)
            {
                var move = _undoStack.Pop();
                var targetTube = _tubes[move.ToTube];
                var sourceTube = _tubes[move.FromTube];

                // Remove from target
                int[] state = targetTube.GetCurrentState();
                int newCount = state.Length - move.MovedLayers.Length;
                int[] newState = new int[newCount];
                System.Array.Copy(state, 0, newState, 0, newCount);
                targetTube.RestoreState(newState);

                // Add back to source
                sourceTube.AddLayers(move.MovedLayers);

                _moveCount--;
                _ui.UpdateMoves(_moveCount);
            }
        }

        private void CheckWinCondition()
        {
            foreach (var tube in _tubes)
            {
                if (!tube.IsEmpty && !tube.IsComplete)
                    return;
            }

            // Level complete!
            int stars = CalculateStars();
            int coinReward = stars * 10;

            // Save progress
            var progress = SaveManager.Instance.Data.GetGameProgress("water_sort");
            if (_currentLevel > progress.HighestLevel)
                progress.HighestLevel = _currentLevel;

            progress.TotalStars += stars;
            progress.LevelResults.Add(new LevelResult
            {
                LevelNumber = _currentLevel,
                Stars = stars,
                Score = _moveCount
            });

            SaveManager.Instance.Save();

            AudioManager.Instance.PlayLevelComplete();
            GameEvents.FireLevelCompleted(stars);
            _ui.ShowLevelComplete(stars, coinReward);
        }

        private int CalculateStars()
        {
            // Optimal moves ~ number of colors * 2
            var (colors, _, _) = LevelGenerator.GetDifficultyForLevel(_currentLevel);
            int optimalMoves = colors * 3;

            if (_moveCount <= optimalMoves) return 3;
            if (_moveCount <= optimalMoves * 1.5f) return 2;
            return 1;
        }

        private void CreateTubes(WaterSortLevel level)
        {
            int totalTubes = level.TubeCount;
            int tubesPerRow = Mathf.Min(totalTubes, _maxTubesPerRow);
            int rows = Mathf.CeilToInt((float)totalTubes / tubesPerRow);

            float totalWidth = (tubesPerRow - 1) * _tubeSpacing;
            float startX = -totalWidth / 2f;

            for (int i = 0; i < totalTubes; i++)
            {
                int row = i / tubesPerRow;
                int col = i % tubesPerRow;

                int tubesInThisRow = (row == rows - 1) ? totalTubes - row * tubesPerRow : tubesPerRow;
                float rowWidth = (tubesInThisRow - 1) * _tubeSpacing;
                float rowStartX = -rowWidth / 2f;

                Vector3 pos = new Vector3(
                    rowStartX + col * _tubeSpacing,
                    -row * 3f,
                    0
                );

                var tubeObj = Instantiate(_tubePrefab, _tubeContainer);
                tubeObj.transform.localPosition = pos;

                var tube = tubeObj.GetComponent<Tube>();

                int[] layers = new int[level.LayersPerTube];
                for (int l = 0; l < level.LayersPerTube; l++)
                {
                    int idx = i * level.LayersPerTube + l;
                    layers[l] = idx < level.TubeData.Length ? level.TubeData[idx] : 0;
                }

                tube.Initialize(i, level.LayersPerTube, layers);
                _tubes.Add(tube);
            }
        }

        private void ClearTubes()
        {
            foreach (var tube in _tubes)
                Destroy(tube.gameObject);
            _tubes.Clear();
        }
    }
}
