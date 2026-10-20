import Svg, { Path } from 'react-native-svg';

// Контурные иконки (набор Lucide, лицензия ISC) на сетке 24×24.
// `fill` — фигура заливается при filled; `inner` — внутренний контур (его при заливке
// приходится рисовать цветом подложки `cutout`, иначе он сливается с заливкой).
type Shape = { d: string; fill?: boolean; inner?: boolean };

const SHAPES = {
  home: [
    {
      d: 'M3 10a2 2 0 0 1 .709-1.528l7-5.999a2 2 0 0 1 2.582 0l7 5.999A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z',
      fill: true,
    },
    { d: 'M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8', inner: true },
  ],
  shirt: [
    {
      d: 'M20.38 3.46 16 2a4 4 0 0 1-8 0L3.62 3.46a2 2 0 0 0-1.34 2.23l.58 3.47a1 1 0 0 0 .99.84H6v10c0 1.1.9 2 2 2h8a2 2 0 0 0 2-2V10h2.15a1 1 0 0 0 .99-.84l.58-3.47a2 2 0 0 0-1.34-2.23z',
      fill: true,
    },
  ],
  scan: [
    { d: 'M3 7V5a2 2 0 0 1 2-2h2' },
    { d: 'M17 3h2a2 2 0 0 1 2 2v2' },
    { d: 'M21 17v2a2 2 0 0 1-2 2h-2' },
    { d: 'M7 21H5a2 2 0 0 1-2-2v-2' },
    { d: 'M12 8a2 2 0 1 0 0 4a2 2 0 1 0 0-4z' },
    { d: 'M8 17c0-2 1.8-3 4-3s4 1 4 3' },
  ],
  heart: [
    {
      d: 'M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z',
      fill: true,
    },
  ],
  user: [
    { d: 'M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2', fill: true },
    { d: 'M12 3a4 4 0 1 0 0 8a4 4 0 1 0 0-8z', fill: true },
  ],
  message: [{ d: 'M7.9 20A9 9 0 1 0 4 16.1L2 22Z' }],
  check: [{ d: 'M20 6 9 17l-5-5' }],
  'arrow-left': [{ d: 'M19 12H5' }, { d: 'm12 19-7-7 7-7' }],
  plus: [{ d: 'M5 12h14' }, { d: 'M12 5v14' }],
  x: [{ d: 'M18 6 6 18' }, { d: 'm6 6 12 12' }],
  camera: [
    { d: 'M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z' },
    { d: 'M12 10a3 3 0 1 0 0 6a3 3 0 1 0 0-6z' },
  ],
  image: [
    { d: 'M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z' },
    { d: 'M9 7a2 2 0 1 0 0 4a2 2 0 1 0 0-4z' },
    { d: 'm21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21' },
  ],
  trash: [
    { d: 'M3 6h18' },
    { d: 'M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6' },
    { d: 'M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2' },
  ],
  'arrow-right': [{ d: 'M5 12h14' }, { d: 'm12 5 7 7-7 7' }],
  // Точки рисуются штрихом с круглыми концами — размер задаётся через strokeWidth.
  ellipsis: [{ d: 'M5 12h.01M12 12h.01M19 12h.01' }],
} satisfies Record<string, Shape[]>;

export type IconName = keyof typeof SHAPES;

type Props = {
  name: IconName;
  color: string;
  size?: number;
  strokeWidth?: number;
  filled?: boolean;
  cutout?: string;
};

export function Icon({ name, color, size = 22, strokeWidth = 1.75, filled = false, cutout }: Props) {
  const shapes: Shape[] = SHAPES[name];

  return (
    <Svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      strokeLinecap="round"
      strokeLinejoin="round">
      {shapes.map((shape, i) => (
        <Path
          key={i}
          d={shape.d}
          stroke={filled && shape.inner && cutout ? cutout : color}
          strokeWidth={strokeWidth}
          fill={filled && shape.fill ? color : 'none'}
        />
      ))}
    </Svg>
  );
}
