# 琴韵 · 古风音乐播放器

基于 **Tauri v2 + Vite 8 + Vue 3** 构建的跨平台古风音乐播放器。

## 功能特性

- ◆ 支持本地音频文件播放（mp3 · flac · wav · ogg · aac · m4a · wma 等主流格式）
- ◆ 支持网络音频地址播放
- ◆ 文件夹扫描批量导入
- ◆ 唱片封面展示（ID3 标签内嵌封面）
- ◆ 滚动歌词展示（LRC 歌词文件 + 内嵌歌词）
- ◆ 四种播放模式：循环 · 单曲 · 随机 · 顺序
- ◆ 古风水墨金玉界面

## 开发

```bash
pnpm install
pnpm tauri dev
```

## 构建

```bash
pnpm tauri build
```