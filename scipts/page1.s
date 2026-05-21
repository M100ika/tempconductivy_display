//=================================================================
// Page 1 — Main Dashboard  (page1.s)
//=================================================================

// Page pre-initialize event
page1.preinitialize:
  currentPage=1
  // Start refresh timer (500ms)
  tm0.en=1
  // Update all sensor displays
  gosub updateDashboard
return

// Timer tm0: Periodic refresh (500ms)
page1.tm0:
  gosub updateDashboard
return

// Subroutine: Update all dashboard values
page1.updateDashboard:
  // T1–T4 cylinder zones
  t1.txt=t1_val+"°C"
  t2.txt=t2_val+"°C"
  t3.txt=t3_val+"°C"
  t4.txt=t4_val+"°C"
  // T5 heater
  t5.txt=t5_val+"°C"
  t5bar.val=t5_val*100/1200
  // Heater status badge
  if(heater_status==1)
  {
    heaterBadge.txt="ACTIVE"
    heaterBadge.bco=1024   // dark green
    heaterBadge.pco=2016   // bright green
  }else if(heater_status==2)
  {
    heaterBadge.txt="ERROR"
    heaterBadge.bco=10240  // dark red
    heaterBadge.pco=63488  // bright red
  }else{
    heaterBadge.txt="IDLE"
    heaterBadge.bco=10537  // dark gray
    heaterBadge.pco=33808  // light gray
  }
return

//--- Navigation buttons ---
page1.btnMain:
  // Already on Main — do nothing or refresh
  gosub updateDashboard
return

page1.btnGraph:
  tm0.en=0
  page 2
return

page1.btnSettings:
  // page 4 used for Error Log per spec; Settings placeholder
  tm0.en=0
  page 4
return

page1.btnLog:
  tm0.en=0
  page 4
return
