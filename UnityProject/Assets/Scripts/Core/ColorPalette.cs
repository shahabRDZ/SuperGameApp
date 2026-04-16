using UnityEngine;

namespace WaterSort.Core
{
    public static class ColorPalette
    {
        public static readonly Color[] LiquidColors = new Color[]
        {
            new Color32(0, 0, 0, 0),         // 0 = empty
            new Color32(120, 215, 50, 255),   // 1 = Bright Green
            new Color32(255, 100, 180, 255),  // 2 = Hot Pink
            new Color32(100, 60, 170, 255),   // 3 = Dark Purple
            new Color32(240, 200, 40, 255),   // 4 = Golden Yellow
            new Color32(40, 90, 220, 255),    // 5 = Royal Blue
            new Color32(230, 55, 45, 255),    // 6 = Red
            new Color32(255, 145, 30, 255),   // 7 = Orange
            new Color32(60, 200, 230, 255),   // 8 = Cyan
            new Color32(240, 140, 200, 255),  // 9 = Light Pink
            new Color32(170, 120, 80, 255),   // 10 = Brown
            new Color32(200, 240, 80, 255),   // 11 = Lime
            new Color32(240, 230, 130, 255),  // 12 = Pale Yellow
        };

        public static Color GetLiquidColor(int id)
        {
            if (id < 0 || id >= LiquidColors.Length) return Color.gray;
            return LiquidColors[id];
        }

        public static Color GetDifficultyColor(string diff)
        {
            switch (diff)
            {
                case "EASY": return new Color32(60, 190, 100, 255);
                case "NORMAL": return new Color32(60, 150, 220, 255);
                case "MEDIUM": return new Color32(220, 190, 40, 255);
                case "HARD": return new Color32(230, 120, 40, 255);
                case "EXPERT": return new Color32(220, 60, 60, 255);
                case "MASTER": return new Color32(190, 60, 170, 255);
                case "INSANE": return new Color32(190, 40, 40, 255);
                default: return Color.white;
            }
        }
    }
}
