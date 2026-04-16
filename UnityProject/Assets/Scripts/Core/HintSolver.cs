using System.Collections.Generic;
using System.Linq;

namespace WaterSort.Core
{
    public static class HintSolver
    {
        public static (int from, int to)? FindHint(List<List<int>> tubes)
        {
            var visited = new HashSet<string>();
            var queue = new Queue<(List<List<int>> state, List<(int, int)> path)>();

            visited.Add(StateKey(tubes));
            queue.Enqueue((DeepCopy(tubes), new List<(int, int)>()));

            int iterations = 0;
            while (queue.Count > 0 && iterations < 12000)
            {
                iterations++;
                var (current, path) = queue.Dequeue();

                foreach (var move in GetMoves(current))
                {
                    var next = DoMove(current, move.from, move.to);
                    var key = StateKey(next);
                    if (visited.Contains(key)) continue;
                    visited.Add(key);

                    var newPath = new List<(int, int)>(path) { move };

                    if (LevelGenerator.AllComplete(next))
                        return newPath[0];

                    queue.Enqueue((next, newPath));
                }
            }

            var fallback = GetMoves(tubes);
            return fallback.Count > 0 ? fallback[0] : null;
        }

        private static List<(int from, int to)> GetMoves(List<List<int>> tubes)
        {
            var moves = new List<(int, int)>();
            for (int f = 0; f < tubes.Count; f++)
            {
                if (tubes[f].Count == 0) continue;
                int top = tubes[f][tubes[f].Count - 1];
                int cnt = 0;
                for (int k = tubes[f].Count - 1; k >= 0 && tubes[f][k] == top; k--) cnt++;

                for (int d = 0; d < tubes.Count; d++)
                {
                    if (f == d || tubes[d].Count >= 4) continue;
                    if (tubes[d].Count == 0)
                    {
                        if (new HashSet<int>(tubes[f]).Count != 1)
                            moves.Add((f, d));
                    }
                    else if (tubes[d][tubes[d].Count - 1] == top && tubes[d].Count + cnt <= 4)
                        moves.Add((f, d));
                }
            }
            return moves;
        }

        private static List<List<int>> DoMove(List<List<int>> tubes, int f, int d)
        {
            var ns = DeepCopy(tubes);
            int top = ns[f][ns[f].Count - 1];
            while (ns[f].Count > 0 && ns[f][ns[f].Count - 1] == top && ns[d].Count < 4)
            {
                ns[d].Add(ns[f][ns[f].Count - 1]);
                ns[f].RemoveAt(ns[f].Count - 1);
            }
            return ns;
        }

        private static List<List<int>> DeepCopy(List<List<int>> tubes)
        {
            return tubes.Select(t => new List<int>(t)).ToList();
        }

        private static string StateKey(List<List<int>> tubes)
        {
            return string.Join("|", tubes.Select(t => string.Join(",", t)));
        }
    }
}
