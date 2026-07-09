Attribute VB_Name = "Revalidate_IR_Swap"
Option Explicit

' IR Swap Revalidation Bridge
' Python remains the pricing engine.
' Excel/VBA is the reviewer bridge for revalidation controls.

Public Sub RunIRSwapRevalidation()
    Dim ws As Worksheet
    Dim logWs As Worksheet
    Dim pvSymmetry As String
    Dim dv01Sign As String
    Dim shockDirection As String
    Dim finalStatus As String

    Set ws = ThisWorkbook.Worksheets("Control_Panel")
    Set logWs = ThisWorkbook.Worksheets("Revalidation_Log")

    pvSymmetry = CheckPVSymmetry(ws.Range("B8").Value)
    dv01Sign = CheckDV01Sign(ws.Range("B9").Value, ws.Range("B10").Value)
    shockDirection = CheckShockDirection(ws.Range("B12").Value, ws.Range("B11").Value)

    ws.Range("E15").Value = pvSymmetry
    ws.Range("E16").Value = dv01Sign
    ws.Range("E17").Value = shockDirection
    ws.Range("E18").Value = "BASE USE ONLY"
    ws.Range("E19").Value = "NOT COVERED"

    If pvSymmetry = "PASS" And dv01Sign = "PASS" And shockDirection = "PASS" Then
        finalStatus = "PASS: base clean-pricing and first-order rate-risk checks validated. XVA remains outside this layer."
    Else
        finalStatus = "REVIEW: one or more base validation controls failed."
    End If

    ws.Range("B22").Value = finalStatus
    AppendRevalidationLog logWs, finalStatus

    MsgBox finalStatus, vbInformation, "IR Swap Revalidation"
End Sub

Private Function CheckPVSymmetry(ByVal symmetryError As Double) As String
    If Abs(symmetryError) <= 1# Then
        CheckPVSymmetry = "PASS"
    Else
        CheckPVSymmetry = "REVIEW"
    End If
End Function

Private Function CheckDV01Sign(ByVal payerDV01 As Double, ByVal receiverDV01 As Double) As String
    If payerDV01 > 0 And receiverDV01 < 0 Then
        CheckDV01Sign = "PASS"
    Else
        CheckDV01Sign = "REVIEW"
    End If
End Function

Private Function CheckShockDirection(ByVal minus100PayerPnL As Double, ByVal plus100PayerPnL As Double) As String
    If minus100PayerPnL < 0 And plus100PayerPnL > 0 Then
        CheckShockDirection = "PASS"
    Else
        CheckShockDirection = "REVIEW"
    End If
End Function

Private Sub AppendRevalidationLog(ByVal logWs As Worksheet, ByVal finalStatus As String)
    Dim nextRow As Long
    nextRow = logWs.Cells(logWs.Rows.Count, 1).End(xlUp).Row + 1

    logWs.Cells(nextRow, 1).Value = Now
    logWs.Cells(nextRow, 2).Value = Environ$("Username")
    logWs.Cells(nextRow, 3).Value = finalStatus
End Sub
