using System.Collections;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using WaterSort.Core;

namespace WaterSort.Game
{
    public class GameManager : MonoBehaviour
    {
        public static GameManager Instance { get; private set; }

        [Header("Prefabs")]
        [SerializeField] private GameObject bottlePrefab;

        [Header("Layout")]
        [SerializeField] private Transform bottleContainer;
        [SerializeField] private float spacing = 1.1f;
        [SerializeField] private int maxPerRow = 5;
        [SerializeField] private float rowGap = 2.5f;

        [Header("Components")]
        [SerializeField] private PourAnimator pourAnimator;

        [Header("Audio")]
        [SerializeField] private AudioSource sfxSource;
        [SerializeField] private AudioClip tapClip;
        [SerializeField] private AudioClip pourClip;
        [SerializeField] private AudioClip splashClip;
        [SerializeField] private AudioClip completeClip;
        [SerializeField] private AudioClip winClip;
        [SerializeField] private AudioClip undoClip;
        [SerializeField] private AudioClip errorClip;

        public GameData Data { get; private set; }
        public int CurrentLevel { get; private set; }
        public int Moves { get; private set; }

        private List<Bottle> _bottles = new List<Bottle>();
        private List<List<List<int>>> _undoStack = new List<List<List<int>>>();
        private Bottle _selected;
        private (int from, int to)? _hintMove;

        // Events
        public System.Action<int> OnMovesChanged;
        public System.Action<int, int> OnLevelComplete; // stars, coins
        public System.Action OnCoinsChanged;

        private void Awake()
        {
            if (Instance == null) { Instance = this; }
            else { Destroy(gameObject); return; }

            Data = SaveSystem.Load();
        }

        public void LoadLevel(int level)
        {
            CurrentLevel = level;
            Moves = 0;
            _undoStack.Clear();
            _selected = null;
            _hintMove = null;

            ClearBottles();

            var tubes = LevelGenerator.Generate(level);
            CreateBottles(tubes);

            OnMovesChanged?.Invoke(0);
        }

        public void OnBottleClicked(Bottle bottle)
        {
            if (pourAnimator != null && pourAnimator.IsAnimating) return;

            PlaySfx(tapClip);

            if (_selected == null)
            {
                if (!bottle.IsEmpty && !bottle.IsComplete)
                {
                    _selected = bottle;
                    bottle.SetSelected(true);
                    ClearHint();
                }
            }
            else if (_selected == bottle)
            {
                _selected.SetSelected(false);
                _selected = null;
            }
            else
            {
                TryPour(_selected, bottle);
            }
        }

        private void TryPour(Bottle source, Bottle target)
        {
            int topColor = source.TopColor;
            int topCount = source.TopColorCount;

            if (!target.CanReceive(topColor) || (target.IsEmpty && source.IsComplete))
            {
                // Invalid move — switch selection
                source.SetSelected(false);
                if (!target.IsEmpty && !target.IsComplete)
                {
                    _selected = target;
                    target.SetSelected(true);
                }
                else
                {
                    _selected = null;
                    PlaySfx(errorClip);
                }
                return;
            }

            source.SetSelected(false);
            _selected = null;

            // Save undo state
            _undoStack.Add(_bottles.Select(b => b.GetState()).ToList());

            if (pourAnimator != null)
            {
                StartCoroutine(pourAnimator.AnimatePour(source, target, () =>
                {
                    ExecutePour(source, target);
                }));
            }
            else
            {
                ExecutePour(source, target);
            }
        }

        private void ExecutePour(Bottle source, Bottle target)
        {
            int[] removed = source.RemoveTop();

            int space = 4 - target.GetState().Count;
            int toAdd = Mathf.Min(removed.Length, space);
            int[] adding = new int[toAdd];
            System.Array.Copy(removed, 0, adding, 0, toAdd);

            if (toAdd < removed.Length)
            {
                int[] excess = new int[removed.Length - toAdd];
                System.Array.Copy(removed, toAdd, excess, 0, excess.Length);
                source.AddLayers(excess);
            }

            target.AddLayers(adding);
            PlaySfx(splashClip);

            Moves++;
            OnMovesChanged?.Invoke(Moves);

            if (target.IsComplete)
                PlaySfx(completeClip);

            // Check win
            if (LevelGenerator.AllComplete(_bottles.Select(b => b.GetState()).ToList()))
            {
                StartCoroutine(WinSequence());
            }
        }

        private IEnumerator WinSequence()
        {
            yield return new WaitForSeconds(0.5f);

            PlaySfx(winClip);

            int stars = CalculateStars();
            int reward = stars * 15;

            Data.Coins += reward;
            Data.SetStars(CurrentLevel, stars);
            if (CurrentLevel >= Data.CurrentLevel)
                Data.CurrentLevel = CurrentLevel + 1;
            SaveSystem.Save(Data);

            OnLevelComplete?.Invoke(stars, reward);
        }

        public int CalculateStars()
        {
            var (colors, _) = LevelGenerator.GetDifficulty(CurrentLevel);
            int optimal = colors * 2;
            if (Moves <= optimal) return 3;
            if (Moves <= optimal * 2) return 2;
            return 1;
        }

        public void Undo()
        {
            if (_undoStack.Count == 0 || (pourAnimator != null && pourAnimator.IsAnimating))
                return;

            if (Data.UndoCount <= 0) { PlaySfx(errorClip); return; }

            var prevState = _undoStack[_undoStack.Count - 1];
            _undoStack.RemoveAt(_undoStack.Count - 1);

            for (int i = 0; i < _bottles.Count && i < prevState.Count; i++)
                _bottles[i].SetState(prevState[i]);

            if (_selected != null) { _selected.SetSelected(false); _selected = null; }
            Moves = Mathf.Max(0, Moves - 1);
            Data.UndoCount--;
            OnMovesChanged?.Invoke(Moves);
            PlaySfx(undoClip);
        }

        public void Restart()
        {
            LoadLevel(CurrentLevel);
        }

        public void GetHint()
        {
            if (Data.HintCount <= 0) { PlaySfx(errorClip); return; }

            var tubes = _bottles.Select(b => b.GetState()).ToList();
            var hint = HintSolver.FindHint(tubes);

            if (hint.HasValue)
            {
                _hintMove = hint;
                Data.HintCount--;
                _bottles[hint.Value.from].SetHintHighlight(true);
                _bottles[hint.Value.to].SetHintHighlight(true);
                PlaySfx(tapClip);
            }
        }

        public void AddExtraTube()
        {
            if (Data.AddTubeCount <= 0) { PlaySfx(errorClip); return; }

            Data.AddTubeCount--;
            var tubes = _bottles.Select(b => b.GetState()).ToList();
            tubes.Add(new List<int>());
            ClearBottles();
            CreateBottles(tubes);
            PlaySfx(tapClip);
        }

        private void ClearHint()
        {
            if (_hintMove.HasValue)
            {
                if (_hintMove.Value.from < _bottles.Count)
                    _bottles[_hintMove.Value.from].SetHintHighlight(false);
                if (_hintMove.Value.to < _bottles.Count)
                    _bottles[_hintMove.Value.to].SetHintHighlight(false);
                _hintMove = null;
            }
        }

        private void CreateBottles(List<List<int>> tubes)
        {
            int n = tubes.Count;
            int perRow = Mathf.Min(n, maxPerRow);
            int rows = Mathf.CeilToInt((float)n / perRow);

            for (int i = 0; i < n; i++)
            {
                int row = i / perRow;
                int col = i % perRow;
                int inRow = Mathf.Min(perRow, n - row * perRow);

                float totalWidth = (inRow - 1) * spacing;
                float startX = -totalWidth / 2f;

                Vector3 pos = new Vector3(
                    startX + col * spacing,
                    -row * rowGap,
                    0
                );

                var obj = Instantiate(bottlePrefab, bottleContainer);
                obj.SetActive(true);
                obj.transform.localPosition = pos;

                var bottle = obj.GetComponent<Bottle>();
                bottle.Init(i, tubes[i]);
                _bottles.Add(bottle);
            }
        }

        private void ClearBottles()
        {
            foreach (var b in _bottles)
                if (b != null) Destroy(b.gameObject);
            _bottles.Clear();
        }

        private void PlaySfx(AudioClip clip)
        {
            if (sfxSource != null && clip != null)
                sfxSource.PlayOneShot(clip);
        }
    }
}
