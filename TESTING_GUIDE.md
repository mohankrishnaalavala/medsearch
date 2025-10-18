# MedSearch AI - Comprehensive Testing Guide

**Application URL:** http://107.178.215.243  
**Testing Date:** October 18, 2025  
**Version:** 1.0.0

---

## 🎯 Testing Objectives

1. Verify all Pillar 3 features (Synthesis Quality & Safety)
2. Verify all Pillar 4 features (Polished UX)
3. Test end-to-end search flow
4. Validate performance and responsiveness
5. Ensure accessibility compliance
6. Confirm error handling and graceful degradation

---

## 📋 Test Cases

### Test Suite 1: Basic Functionality

#### TC1.1: Homepage Load
**Steps:**
1. Open http://107.178.215.243 in browser
2. Verify page loads within 2 seconds
3. Check that chat interface is visible

**Expected Result:**
- ✅ Page loads successfully
- ✅ Chat interface displays with input field
- ✅ No console errors
- ✅ Responsive layout on mobile/desktop

**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

---

#### TC1.2: Simple Search Query
**Steps:**
1. Enter query: "Type 2 diabetes treatment"
2. Click search or press Enter
3. Wait for results

**Expected Result:**
- ✅ Search initiates immediately
- ✅ Skeleton UI shows while loading
- ✅ Results appear within 3 seconds
- ✅ Citations are displayed with numbers [1], [2], [3]

**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

---

### Test Suite 2: Pillar 3 Features (Synthesis Quality & Safety)

#### TC2.1: Grounded Citations (T3.1)
**Steps:**
1. Search for "diabetes treatment guidelines"
2. Review synthesis response
3. Check for inline citations

**Expected Result:**
- ✅ Every factual claim has citation [1], [2], etc.
- ✅ Citations are clickable
- ✅ Citation cards show full metadata
- ✅ No unsupported claims

**Verification Points:**
- [ ] At least 3 citations in synthesis
- [ ] All citations have source metadata
- [ ] Citations link to correct sources

**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

---

#### TC2.2: Conflict Detection (T3.2)
**Steps:**
1. Search for controversial topic: "metformin vs insulin for elderly"
2. Check for conflict detection panel
3. Review consensus summary

**Expected Result:**
- ✅ Conflict panel appears if contradictory sources found
- ✅ Consensus summary provided
- ✅ Both viewpoints represented fairly

**Verification Points:**
- [ ] Conflict panel visible (if applicable)
- [ ] Consensus text is clear
- [ ] Sources for each viewpoint listed

**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

---

#### TC2.3: Confidence Bands (T3.3)
**Steps:**
1. Search for well-researched topic: "aspirin for heart disease"
2. Check confidence indicator
3. Note confidence level (Low/Medium/High)

**Expected Result:**
- ✅ Confidence band displayed
- ✅ Level is appropriate for evidence quality
- ✅ Explanation provided for confidence level

**Verification Points:**
- [ ] Confidence badge visible
- [ ] Level matches evidence (High for well-researched topics)
- [ ] Tooltip explains confidence calculation

**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

---

#### TC2.4: Filter Propagation (T3.4)
**Steps:**
1. Apply filters: Year range (2020-2024), Study type (RCT)
2. Submit search query
3. Verify filters affect results

**Expected Result:**
- ✅ Only results matching filters appear
- ✅ Synthesis acknowledges filter constraints
- ✅ Citation cards show filtered metadata

**Verification Points:**
- [ ] All results within year range
- [ ] Only RCT studies shown
- [ ] Synthesis mentions filter constraints

**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

---

#### TC2.5: Safety Guardrails (T3.5)
**Steps:**
1. Check for medical disclaimer
2. Try rapid-fire queries (rate limiting)
3. Search for sensitive medical terms

**Expected Result:**
- ✅ Medical disclaimer visible
- ✅ Rate limiting prevents abuse
- ✅ Unsafe content handled appropriately
- ✅ No PII in logs

**Verification Points:**
- [ ] Disclaimer: "Not medical advice" visible
- [ ] Rate limit triggers after X requests
- [ ] Sensitive queries handled safely

**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

---

### Test Suite 3: Pillar 4 Features (Polished UX)

#### TC3.1: Metadata Badges (T4.1)
**Steps:**
1. Perform search
2. Examine citation cards
3. Check for year and study type badges

**Expected Result:**
- ✅ Year badge visible (e.g., "2023")
- ✅ Study type badge visible (e.g., "Clinical Trial")
- ✅ Badges are color-coded and clear

**Verification Points:**
- [ ] Year badge present on all citations
- [ ] Study type badge present
- [ ] Badges are visually distinct

**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

---

#### TC3.2: Hover Preview (T4.1)
**Steps:**
1. Hover over citation card
2. Check for preview tooltip
3. Verify preview content

**Expected Result:**
- ✅ Tooltip appears on hover
- ✅ Shows abstract snippet
- ✅ Shows authors and journal
- ✅ Copy citation button works

**Verification Points:**
- [ ] Tooltip appears within 500ms
- [ ] Abstract snippet is readable
- [ ] Copy button copies full citation

**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

---

#### TC3.3: URL Filters (T4.2)
**Steps:**
1. Apply filters (sources, year, study type)
2. Check URL for query parameters
3. Copy URL and open in new tab
4. Verify filters persist

**Expected Result:**
- ✅ URL updates with filter parameters
- ✅ Shared URL preserves filter state
- ✅ Filters apply automatically on page load

**Verification Points:**
- [ ] URL contains filter params (e.g., ?sources=pubmed&year=2020-2024)
- [ ] Shared URL works in incognito mode
- [ ] Filters restore correctly

**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

---

#### TC3.4: Streaming Polish (T4.3)
**Steps:**
1. Submit search query
2. Observe loading states
3. Check for skeleton UI
4. Verify error handling

**Expected Result:**
- ✅ Skeleton UI appears immediately
- ✅ First token visible < 1.5s
- ✅ Smooth streaming animation
- ✅ Error toast with retry button

**Verification Points:**
- [ ] Skeleton UI shows while loading
- [ ] Streaming is smooth (no jank)
- [ ] Error handling works (disconnect network)

**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

---

#### TC3.5: Accessibility (T4.4)
**Steps:**
1. Navigate using keyboard only (Tab, Enter, Esc)
2. Use screen reader (VoiceOver/NVDA)
3. Check ARIA live regions
4. Test on mobile device

**Expected Result:**
- ✅ All interactive elements keyboard accessible
- ✅ Screen reader announces updates
- ✅ ARIA live regions for dynamic content
- ✅ Mobile layout is usable

**Verification Points:**
- [ ] Can navigate entire app with keyboard
- [ ] Screen reader reads all content
- [ ] Focus indicators visible
- [ ] Mobile responsive (< 768px width)

**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

---

### Test Suite 4: Performance Testing

#### TC4.1: Response Time
**Steps:**
1. Measure time to first byte (TTFB)
2. Measure time to first contentful paint (FCP)
3. Measure time to interactive (TTI)

**Expected Result:**
- ✅ TTFB < 500ms
- ✅ FCP < 1.5s
- ✅ TTI < 3s

**Actual Results:**
- TTFB: _____ ms
- FCP: _____ ms
- TTI: _____ ms

**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

---

#### TC4.2: Search Latency
**Steps:**
1. Submit search query
2. Measure time to first token
3. Measure time to complete response

**Expected Result:**
- ✅ First token < 1.5s (p50)
- ✅ Complete response < 5s (p95)

**Actual Results:**
- First token: _____ ms
- Complete response: _____ ms

**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

---

### Test Suite 5: Error Handling & Edge Cases

#### TC5.1: Network Failure
**Steps:**
1. Start search query
2. Disconnect network mid-search
3. Check error handling

**Expected Result:**
- ✅ Error toast appears
- ✅ Retry button available
- ✅ Previous results preserved
- ✅ No app crash

**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

---

#### TC5.2: Empty Results
**Steps:**
1. Search for nonsense query: "xyzabc123"
2. Check empty state handling

**Expected Result:**
- ✅ Friendly "no results" message
- ✅ Suggestions for better search
- ✅ No error thrown

**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

---

#### TC5.3: Service Degradation
**Steps:**
1. Check health endpoint
2. Note degraded services (e.g., Vertex AI)
3. Verify app still functions

**Expected Result:**
- ✅ App uses mock data fallback
- ✅ User sees results (even if mock)
- ✅ Graceful degradation message

**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

---

## 🔍 Manual Testing Checklist

### Visual Testing
- [ ] UI matches design mockups
- [ ] Colors are consistent
- [ ] Typography is readable
- [ ] Spacing is appropriate
- [ ] Icons are clear
- [ ] Animations are smooth

### Cross-Browser Testing
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile Safari (iOS)
- [ ] Mobile Chrome (Android)

### Responsive Testing
- [ ] Desktop (1920x1080)
- [ ] Laptop (1366x768)
- [ ] Tablet (768x1024)
- [ ] Mobile (375x667)
- [ ] Mobile landscape

---

## 📊 Test Results Summary

### Overall Status
- **Total Test Cases:** 20
- **Passed:** ___
- **Failed:** ___
- **Not Tested:** ___
- **Pass Rate:** ___%

### Critical Issues
1. _____
2. _____
3. _____

### Non-Critical Issues
1. _____
2. _____
3. _____

### Recommendations
1. _____
2. _____
3. _____

---

## 🚀 Quick Test Commands

### Test Health Endpoint
```bash
curl http://107.178.215.243/health | jq '.'
```

### Test Search API
```bash
curl -X POST http://107.178.215.243/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "diabetes treatment", "max_results": 5}' | jq '.'
```

### Test Frontend
```bash
curl -I http://107.178.215.243/
```

### Performance Test
```bash
time curl -s http://107.178.215.243/ > /dev/null
```

---

## 📝 Notes

- All tests should be performed on http://107.178.215.243
- Document any issues in GitHub Issues
- Take screenshots for visual bugs
- Record videos for complex issues
- Test on multiple devices and browsers

---

**Happy Testing! 🧪**

