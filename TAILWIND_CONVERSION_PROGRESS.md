# Tailwind to Bootstrap Conversion Progress

## ✅ Files Completed

### 1. **advanced_tracking.html** ✅
- Replaced all Tailwind classes with Bootstrap 5
- Converted grid system: `grid grid-cols-*` → `row` + `col-*`
- Converted flex utilities: `flex items-center` → `d-flex align-items-center`
- Converted spacing: Tailwind spacing → Bootstrap spacing
- Converted colors: `text-gray-300` → inline styles with rgba
- Converted buttons: `bg-blue-500 hover:bg-blue-600` → `btn btn-primary`
- Converted SVG sizes: `w-4 h-4` → inline `style="width: 16px; height: 16px;"`

---

## 🔄 Files In Progress

### 2. **track_request_dashboard.html**
**Tailwind classes found:**
- Line 397: `bg-red-500/20 hover:bg-red-500/30 rounded-lg text-sm`
- Line 409: `text-gray-400`
- Line 418: `bg-red-500 emergency-pulse`

**Status:** Need to convert

### 3. **home.html**
**Tailwind classes found:**
- Line 974, 1023, 1494: SVG with `w-5 h-5` and `w-4 h-4`

**Status:** Need to convert

### 4. **donor_profile.html**
**Status:** Has linter errors (Django template syntax) - needs fixing

### 5. **donor_search.html**
**Tailwind classes found:**
- Multiple instances of Tailwind grid and flex classes

**Status:** Need to convert

---

## 📋 Tailwind → Bootstrap Conversion Guide

### Layout
```html
<!-- Tailwind -->
<div class="flex flex-col lg:flex-row">
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3">

<!-- Bootstrap -->
<div class="d-flex flex-column flex-lg-row">
<div class="row">
  <div class="col-12 col-md-6 col-lg-4">
```

### Spacing
```html
<!-- Tailwind -->
<div class="p-4 m-2 gap-3">

<!-- Bootstrap -->
<div class="p-3 m-1 gap-3">
```

### Typography
```html
<!-- Tailwind -->
<h3 class="text-xl font-bold text-gray-300">

<!-- Bootstrap -->
<h3 class="fs-5 fw-bold" style="color: rgba(255,255,255,0.7);">
```

### Colors
```html
<!-- Tailwind -->
<div class="text-red-400 bg-blue-500">

<!-- Bootstrap -->
<div class="text-primary bg-primary">
<!-- OR inline for custom colors -->
<div style="color: rgba(239, 68, 68, 0.7); background: rgba(59, 130, 246, 0.8);">
```

### Buttons
```html
<!-- Tailwind -->
<button class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg">

<!-- Bootstrap -->
<button class="btn btn-primary">
```

### SVG Icons
```html
<!-- Tailwind -->
<svg class="w-4 h-4 text-red-400">

<!-- Bootstrap -->
<svg style="width: 16px; height: 16px;" class="text-danger">
```

---

## 🎯 Priority Order

1. ✅ **advanced_tracking.html** - DONE
2. 🔧 **donor_profile.html** - Fix linter errors
3. 🔧 **track_request_dashboard.html** - Convert Tailwind
4. 🔧 **home.html** - Convert SVG classes
5. 🔧 **donor_search.html** - Convert Tailwind

---

## 📊 Statistics

- **Total files with Tailwind:** 5 template files
- **Files completed:** 1
- **Files remaining:** 4
- **Tailwind classes replaced:** ~50+
- **Bootstrap classes added:** ~50+

---

## ✨ Key Conversions Made

| Tailwind | Bootstrap | Location |
|----------|-----------|----------|
| `flex flex-col` | `d-flex flex-column` | advanced_tracking.html |
| `lg:flex-row` | `flex-lg-row` | advanced_tracking.html |
| `items-center` | `align-items-center` | advanced_tracking.html |
| `gap-3` | `gap-3` (same) | advanced_tracking.html |
| `text-xl` | `fs-5` | advanced_tracking.html |
| `font-bold` | `fw-bold` | advanced_tracking.html |
| `text-gray-300` | `style="color: rgba(255,255,255,0.7)"` | advanced_tracking.html |
| `w-4 h-4` | `style="width: 16px; height: 16px"` | advanced_tracking.html |
| `bg-blue-500` | `btn btn-primary` | advanced_tracking.html |
| `rounded-lg` | `btn` (includes rounding) | advanced_tracking.html |
| `grid grid-cols-3` | `row` + `col-4` | advanced_tracking.html |
| `text-sm` | `small` | advanced_tracking.html |

---

**Last Updated:** 2026-04-16
**Status:** In Progress - 20% Complete
