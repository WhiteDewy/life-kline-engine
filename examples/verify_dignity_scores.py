
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from life_kline.dignities import (
    compute_essential_dignity_raw,
    compute_accidental_dignity_raw,
    get_term_lord,
    get_face_lord
)
from life_kline.constants import Planet, Sign, CalculationMode
from life_kline.models import PlanetInfo

def test_essential_dignities():
    print("Testing Essential Dignities...")
    
    # 1. Domicile (Temple) +5
    # Sun in Leo
    score = compute_essential_dignity_raw(Planet.SUN, Sign.LEO, 10.0, True)
    print(f"Domicile (Sun in Leo): {score} (Expected: 5.0)")
    
    # 2. Exaltation (Wang) +4
    # Sun in Aries
    score = compute_essential_dignity_raw(Planet.SUN, Sign.ARIES, 10.0, True)
    # Sun in Aries is also Triplicity in Day (+3) and Face (+0.5 potentially).
    # Let's check a pure Exaltation if possible, or just calculate what it should be.
    # Sun in Aries: Exaltation (+4) + Triplicity Day (+3) = 7.0? 
    # Let's check just the Exaltation component by manually checking code logic or using a planet that has fewer dignities.
    # Or just interpret the output log which prints components.
    
    # 3. Term (Jie) +1.5
    # Find a position where a planet is ONLY Term lord and nothing else.
    # Jupiter in Aries 0-6 is Term lord.
    # Jupiter in Aries: Not Domicile, Not Exaltation.
    # Triplicity: Aries (Fire) -> Day: Sun, Night: Jupiter. 
    # So if Night chart, Jupiter is Triplicity (+3).
    # Let's use Day chart. Jupiter in Aries Day chart.
    # Jupiter in Aries 3.0 (Term Lord).
    # Jupiter Face in Aries: Mars, Sun, Venus. Not Face lord.
    # So Jupiter in Aries 3.0 Day chart should be Term (+1.5) - Peregrine check?
    # If it has Term, it is not Peregrine.
    score = compute_essential_dignity_raw(Planet.JUPITER, Sign.ARIES, 3.0, True) # Day chart
    print(f"Term (Jupiter in Aries 3.0 Day): {score} (Expected: 1.5)")

    # 4. Face (Mian) +0.5
    # Mars in Aries 0-10 is Face lord. Also Domicile.
    # Let's find a Face lord that has no other dignity.
    # Mars in Gemini 20-30? No.
    # Let's look at Face table:
    # Aries: Mars, Sun, Venus
    # Taurus: Mercury, Moon, Saturn
    # ...
    # Let's try Sun in Gemini 10-20. Face lord is Sun (Wait, Gemini faces: Jupiter, Mars, Sun).
    # Gemini Decans: Jupiter, Mars, Sun. So Sun is 20-30.
    # Sun in Gemini 25.0.
    # Domicile: No. Exaltation: No.
    # Triplicity (Air): Day=Saturn, Night=Mercury, Part=Jupiter. Sun is none.
    # Term (Gemini): 24-30 is Saturn.
    # So Sun in Gemini 25.0 should have Face (+0.5) only.
    score = compute_essential_dignity_raw(Planet.SUN, Sign.GEMINI, 25.0, True)
    print(f"Face (Sun in Gemini 25.0): {score} (Expected: 0.5)")

    # 5. Peregrine (Wander) -1.5
    # Sun in Libra (Fall -3).
    # Sun in Taurus. 
    # Domicile: No. Exaltation: No.
    # Triplicity (Earth): Day=Venus, Night=Moon, Part=Mars.
    # Term (Taurus): 27-30 Mars.
    # Face (Taurus): 10-20 Moon.
    # Sun in Taurus 15.0.
    # Face: Moon. Term: Jupiter (14-22).
    # So Sun in Taurus 15.0 has no dignity -> Peregrine.
    score = compute_essential_dignity_raw(Planet.SUN, Sign.TAURUS, 15.0, True)
    print(f"Peregrine (Sun in Taurus 15.0): {score} (Expected: -1.5)")

    # 6. Detriment (Loss) -4
    # Sun in Aquarius.
    score = compute_essential_dignity_raw(Planet.SUN, Sign.AQUARIUS, 15.0, True)
    # Note: might have other accidental things or minor dignities, but base is -4.
    # Sun in Aquarius: Detriment (-4). 
    # Peregrine? If it has Detriment, is it Peregrine? Usually Peregrine is "no essential dignity". 
    # Detriment is a debility. Debility does not prevent Peregrine in some systems, but usually Peregrine means "no dignity".
    # If it has Detriment, it definitely has no dignity (unless it has Face/Term etc.).
    # Let's assume the code subtracts for Peregrine if no positive dignity.
    # Sun in Aquarius 15.0:
    # Face: 10-20 Mercury. Term: 13-20 Jupiter.
    # Triplicity: Air (Day Saturn).
    # So Sun has nothing positive. 
    # Score = Detriment (-4) + Peregrine (-1.5) = -5.5? 
    # Let's check logic: is_peregrine checks for Domicile, Exalt, Trip, Term, Face.
    # If none, it returns True.
    # So yes, it will be -5.5.
    print(f"Detriment + Peregrine (Sun in Aquarius 15.0): {score} (Expected: -5.5)")

    # 7. Fall (Sink) -3
    # Sun in Libra.
    # Fall (-3). Peregrine (-1.5). Total -4.5.
    score = compute_essential_dignity_raw(Planet.SUN, Sign.LIBRA, 15.0, True)
    print(f"Fall + Peregrine (Sun in Libra 15.0): {score} (Expected: -4.5)")

def test_accidental_dignities():
    print("\nTesting Accidental Dignities...")
    
    chart_info = {'sun_longitude': 0.0, 'is_day': True} # Sun at Aries 0
    
    # 1. Cazimi +3
    # Planet at Aries 0.1
    p = PlanetInfo(Sign.ARIES, 0.1, 1) # House 1 (Angular +2)
    p.name = "Mercury"
    p.speed = 1.383
    p.is_retrograde = False
    p.latitude = 0
    # Cazimi check needs planet enum. We can pass Mercury.
    # Mercury in 1st house is Joy (+0.5).
    # Angular (+2).
    # Cazimi (+3).
    # Total = 5.5.
    # Clamped to 5.0.
    # But wait, Sun is at 0.0. Mercury at 0.1.
    # Combust/UnderBeams mutually exclusive with Cazimi.
    # Oriental/Occidental: 0.1 - 0.0 = 0.1 (East). +0.5.
    # So: Angular(2) + Cazimi(3) + Joy(0.5) + Oriental(0.5) = 6.0.
    # Clamped to 5.0.
    score = compute_accidental_dignity_raw(p, chart_info)
    print(f"Cazimi + Angular + Joy + Oriental (Mercury): {score} (Expected: 5.0 due to clamp)")

    # 2. Combust -3
    # Planet at Aries 5.0
    p = PlanetInfo(Sign.ARIES, 5.0, 2) # House 2 (Succedent +1)
    p.name = "Mercury"
    p.speed = 1.383
    # Sun 0.0. Planet 5.0. Diff 5.0. Combust.
    # Succedent (+1).
    # Combust (-3).
    # Oriental (+0.5).
    # Joy? Mercury Joy is 1st. This is 2nd. No joy.
    # Total = 1 - 3 + 0.5 = -1.5.
    score = compute_accidental_dignity_raw(p, chart_info)
    print(f"Combust + Succedent + Oriental (Mercury): {score} (Expected: -1.5)")

    # 3. Under Beams -1
    # Planet at Aries 10.0
    p = PlanetInfo(Sign.ARIES, 10.0, 3) # House 3 (Cadent -1)
    p.name = "Mercury"
    p.speed = 1.383
    # Sun 0.0. Planet 10.0. Under Beams.
    # Cadent (-1).
    # Under Beams (-1).
    # Oriental (+0.5).
    # Joy (Moon in 3rd). Let's use Mercury, no joy.
    # Total = -1 - 1 + 0.5 = -1.5.
    score = compute_accidental_dignity_raw(p, chart_info)
    print(f"Under Beams + Cadent + Oriental (Mercury): {score} (Expected: -1.5)")
    
    # 4. Retrograde -1.5
    p = PlanetInfo(Sign.ARIES, 20.0, 6) # House 6 (Cadent -1)
    p.name = "Mars"
    p.is_retrograde = True
    p.speed = -0.5 # Slow
    # Sun 0.0. Planet 20.0. Not under beams (>17).
    # Cadent (-1).
    # Retrograde (-1.5).
    # Oriental (+0.5).
    # Speed: -0.5 / 1.383 < 0.8 -> Slow (-0.5).
    # Mars Joy is 6th. Let's use Mars.
    # Mars in 6th -> Joy (+0.5).
    # Total = -1 (Cad) - 1.5 (Rx) + 0.5 (Ori) - 0.5 (Slow) + 0.5 (Joy) = -2.0.
    score = compute_accidental_dignity_raw(p, chart_info)
    print(f"Retrograde + Cadent + Oriental + Slow + Joy (Mars): {score} (Expected: -2.0)")

    # 6. Oriental/Western Test
    print("\nTesting Oriental/Western Logic...")
    # Case A: Oriental (Rising Before Sun)
    # Sun at 10 Aries (10.0), Planet at 5 Aries (5.0). 
    # Sun - Planet = 5.0 (< 180). Oriental. Score should include +0.5.
    p_ori = PlanetInfo(Sign.ARIES, 5.0, 1)
    p_ori.name = "Mars" # Superior planet
    chart_ori = {'sun_longitude': 10.0, 'is_day': True}
    score_ori = compute_accidental_dignity_raw(p_ori, chart_ori)
    # Base: Angular(+2) + Oriental(+0.5) + Joy(Mars in 6th? No, 1st) = 2.5
    # Wait, Mars Joy is 6th. 
    # Mars in 1st is Angular.
    print(f"Oriental (Mars at 5, Sun at 10): {score_ori} (Expected ~2.5)")

    # Case B: Occidental (Rising After Sun)
    # Sun at 10 Aries (10.0), Planet at 15 Aries (15.0).
    # Sun - Planet = -5 = 355 (> 180). Occidental. Score should include -0.5.
    p_occ = PlanetInfo(Sign.ARIES, 15.0, 1)
    p_occ.name = "Mars"
    chart_occ = {'sun_longitude': 10.0, 'is_day': True}
    # Note: Planet is Under Beams (diff 5 < 8.5 Combust? Yes 5 is Combust).
    # Combust is -3.
    # Angular +2. Occidental -0.5. Combust -3. Total -1.5.
    score_occ = compute_accidental_dignity_raw(p_occ, chart_occ)
    print(f"Occidental (Mars at 15, Sun at 10): {score_occ} (Expected: 2 - 0.5 - 3 = -1.5)")
    
    # Case C: Oriental but far (Not Combust)
    # Sun at 10 Aries (10.0). Planet at 10 Pisces (340.0).
    # Sun - Planet = 10 - 340 = -330 = 30. Oriental.
    # Diff = 30 (> 17, not Under Beams).
    p_ori_far = PlanetInfo(Sign.PISCES, 10.0, 12) # 12th House (Cadent -1) + Joy(Saturn)
    p_ori_far.name = "Saturn"
    chart_ori_far = {'sun_longitude': 10.0, 'is_day': True}
    # Cadent -1. Joy(Saturn in 12) +0.5. Oriental +0.5. Total 0.0.
    score_ori_far = compute_accidental_dignity_raw(p_ori_far, chart_ori_far)
    print(f"Oriental Far (Saturn at 340, Sun at 10): {score_ori_far} (Expected: -1 + 0.5 + 0.5 = 0.0)")

if __name__ == "__main__":
    test_essential_dignities()
    test_accidental_dignities()
