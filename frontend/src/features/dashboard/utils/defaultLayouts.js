/**
 * defaultLayouts - Default widget positions per breakpoint for react-grid-layout
 *
 * 12-col at lg, 6-col at sm, 2-col at xs.
 * Each item: { i: widgetId, x, y, w, h, minW?, minH? }
 */

export const BREAKPOINTS = { lg: 1100, sm: 768, xs: 0 };
export const COLS = { lg: 12, sm: 6, xs: 2 };
export const ROW_HEIGHT = 80;
export const MARGIN = [16, 16];

export const DEFAULT_LAYOUTS = {
  lg: [
    { i: 'brain-focus',    x: 0,  y: 0, w: 6, h: 3, minW: 3, minH: 2 },
    { i: 'quick-capture',  x: 6,  y: 0, w: 3, h: 3, minW: 2, minH: 2 },
    { i: 'calendar',       x: 9,  y: 0, w: 3, h: 3, minW: 2, minH: 2 },
    { i: 'favorites',      x: 0,  y: 3, w: 6, h: 3, minW: 3, minH: 2 },
    { i: 'tasks',          x: 6,  y: 3, w: 3, h: 3, minW: 2, minH: 2 },
    { i: 'quick-upload',   x: 9,  y: 3, w: 3, h: 3, minW: 2, minH: 2 },
    { i: 'knowledge-graph',x: 0,  y: 6, w: 6, h: 3, minW: 3, minH: 2 },
    { i: 'system-status',  x: 6,  y: 6, w: 6, h: 3, minW: 3, minH: 2 },
    { i: 'recent-notes',   x: 0,  y: 9, w: 4, h: 3, minW: 2, minH: 2 },
    { i: 'top-tags',       x: 4,  y: 9, w: 4, h: 3, minW: 2, minH: 2 },
    { i: 'most-connected', x: 8,  y: 9, w: 4, h: 3, minW: 2, minH: 2 },
    { i: 'ai-activity',    x: 0, y: 12, w: 6, h: 3, minW: 3, minH: 2 },
  ],
  sm: [
    { i: 'brain-focus',    x: 0, y: 0,  w: 6, h: 3, minW: 2, minH: 2 },
    { i: 'quick-capture',  x: 0, y: 3,  w: 3, h: 3, minW: 2, minH: 2 },
    { i: 'calendar',       x: 3, y: 3,  w: 3, h: 3, minW: 2, minH: 2 },
    { i: 'favorites',      x: 0, y: 6,  w: 6, h: 3, minW: 2, minH: 2 },
    { i: 'tasks',          x: 0, y: 9,  w: 3, h: 3, minW: 2, minH: 2 },
    { i: 'quick-upload',   x: 3, y: 9,  w: 3, h: 3, minW: 2, minH: 2 },
    { i: 'knowledge-graph',x: 0, y: 12, w: 6, h: 3, minW: 2, minH: 2 },
    { i: 'system-status',  x: 0, y: 15, w: 6, h: 3, minW: 2, minH: 2 },
    { i: 'recent-notes',   x: 0, y: 18, w: 3, h: 3, minW: 2, minH: 2 },
    { i: 'top-tags',       x: 3, y: 18, w: 3, h: 3, minW: 2, minH: 2 },
    { i: 'most-connected', x: 0, y: 21, w: 3, h: 3, minW: 2, minH: 2 },
    { i: 'ai-activity',    x: 3, y: 21, w: 3, h: 3, minW: 2, minH: 2 },
  ],
  xs: [
    { i: 'brain-focus',    x: 0, y: 0,  w: 2, h: 3, minW: 2, minH: 2 },
    { i: 'quick-capture',  x: 0, y: 3,  w: 2, h: 3, minW: 2, minH: 2 },
    { i: 'calendar',       x: 0, y: 6,  w: 2, h: 3, minW: 2, minH: 2 },
    { i: 'favorites',      x: 0, y: 9,  w: 2, h: 3, minW: 2, minH: 2 },
    { i: 'tasks',          x: 0, y: 12, w: 2, h: 3, minW: 2, minH: 2 },
    { i: 'quick-upload',   x: 0, y: 15, w: 2, h: 3, minW: 2, minH: 2 },
    { i: 'knowledge-graph',x: 0, y: 18, w: 2, h: 3, minW: 2, minH: 2 },
    { i: 'system-status',  x: 0, y: 21, w: 2, h: 3, minW: 2, minH: 2 },
    { i: 'recent-notes',   x: 0, y: 24, w: 2, h: 3, minW: 2, minH: 2 },
    { i: 'top-tags',       x: 0, y: 27, w: 2, h: 3, minW: 2, minH: 2 },
    { i: 'most-connected', x: 0, y: 30, w: 2, h: 3, minW: 2, minH: 2 },
    { i: 'ai-activity',    x: 0, y: 33, w: 2, h: 3, minW: 2, minH: 2 },
  ],
};
