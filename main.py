import io
import asyncio
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import edge_tts

app = FastAPI(
    title="Edge Neural TTS API",
    version="1.0.0",
    description="Vercel-safe TTS with REAL voice changes"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------
# 25+ REAL NEURAL VOICES
# ------------------------------------
VOICES = {
    "af_za_female": "af-ZA-AdriNeural3 (Female)",
    "am_et_female": "am-ET-MekdesNeural3 (Female)",
    "ar_ae_female": "ar-AE-FatimaNeural (Female)",
    "ar_bh_female": "ar-BH-LailaNeural (Female)",
    "ar_dz_female": "ar-DZ-AminaNeural (Female)",
    "ar_eg_female": "ar-EG-SalmaNeural (Female)",
    "ar_iq_female": "ar-IQ-RanaNeural (Female)",
    "ar_jo_female": "ar-JO-SanaNeural (Female)",
    "ar_kw_female": "ar-KW-NouraNeural (Female)",
    "ar_lb_female": "ar-LB-LaylaNeural (Female)",
    "ar_ly_female": "ar-LY-ImanNeural (Female)",
    "ar_ma_female": "ar-MA-MounaNeural (Female)",
    "ar_om_female": "ar-OM-AyshaNeural (Female)",
    "ar_qa_female": "ar-QA-AmalNeural (Female)",
    "ar_sa_female": "ar-SA-ZariyahNeural (Female)",
    "ar_sy_female": "ar-SY-AmanyNeural (Female)",
    "ar_tn_female": "ar-TN-ReemNeural (Female)",
    "ar_ye_female": "ar-YE-MaryamNeural (Female)",
    "as_in_female": "as-IN-YashicaNeural3 (Female)",
    "az_az_female": "az-AZ-BanuNeural3 (Female)",
    "bg_bg_female": "bg-BG-KalinaNeural (Female)",
    "bn_bd_female": "bn-BD-NabanitaNeural3 (Female)",
    "bn_in_female": "bn-IN-TanishaaNeural3 (Female)",
    "bs_ba_female": "bs-BA-VesnaNeural3 (Female)",
    "ca_es_female": "ca-ES-JoanaNeural (Female)",
    "cs_cz_female": "cs-CZ-VlastaNeural (Female)",
    "cy_gb_female": "cy-GB-NiaNeural3 (Female)",
    "da_dk_female": "da-DK-ChristelNeural (Female)",
    "de_at_female": "de-AT-IngridNeural (Female)",
    "de_ch_female": "de-CH-LeniNeural (Female)",
    "de_de_female": "de-DE-KatjaNeural (Female)",
    "el_gr_female": "el-GR-AthinaNeural (Female)",
    "en_au_female": "en-AU-NatashaNeural (Female)",
    "en_ca_female": "en-CA-ClaraNeural (Female)",
    "en_gb_female": "en-GB-SoniaNeural (Female)",
    "en_hk_female": "en-HK-YanNeural (Female)",
    "en_ie_female": "en-IE-EmilyNeural (Female)",
    "en_in_female": "en-IN-AartiIndicNeural (Female)",
    "en_ke_female": "en-KE-AsiliaNeural (Female)",
    "en_ng_female": "en-NG-EzinneNeural (Female)",
    "en_nz_female": "en-NZ-MollyNeural (Female)",
    "en_ph_female": "en-PH-RosaNeural (Female)",
    "en_sg_female": "en-SG-LunaNeural (Female)",
    "en_tz_female": "en-TZ-ImaniNeural (Female)",
    "en_us_female": "en-US-AvaMultilingualNeural4 (Female)",
    "en_za_female": "en-ZA-LeahNeural (Female)",
    "es_ar_female": "es-AR-ElenaNeural (Female)",
    "es_bo_female": "es-BO-SofiaNeural (Female)",
    "es_cl_female": "es-CL-CatalinaNeural (Female)",
    "es_co_female": "es-CO-SalomeNeural (Female)",
    "es_cr_female": "es-CR-MariaNeural (Female)",
    "es_cu_female": "es-CU-BelkysNeural (Female)",
    "es_do_female": "es-DO-RamonaNeural (Female)",
    "es_ec_female": "es-EC-AndreaNeural (Female)",
    "es_es_female": "es-ES-ElviraNeural (Female)",
    "es_gq_female": "es-GQ-TeresaNeural (Female)",
    "es_gt_female": "es-GT-MartaNeural (Female)",
    "es_hn_female": "es-HN-KarlaNeural (Female)",
    "es_mx_female": "es-MX-DaliaNeural (Female)",
    "es_ni_female": "es-NI-YolandaNeural (Female)",
    "es_pa_female": "es-PA-MargaritaNeural (Female)",
    "es_pe_female": "es-PE-CamilaNeural (Female)",
    "es_pr_female": "es-PR-KarinaNeural (Female)",
    "es_py_female": "es-PY-TaniaNeural (Female)",
    "es_sv_female": "es-SV-LorenaNeural (Female)",
    "es_us_female": "es-US-PalomaNeural (Female)",
    "es_uy_female": "es-UY-ValentinaNeural (Female)",
    "es_ve_female": "es-VE-PaolaNeural (Female)",
    "et_ee_female": "et-EE-AnuNeural3 (Female)",
    "eu_es_female": "eu-ES-AinhoaNeural3 (Female)",
    "fa_ir_female": "fa-IR-DilaraNeural3 (Female)",
    "fi_fi_female": "fi-FI-SelmaNeural (Female)",
    "fil_ph_female": "fil-PH-BlessicaNeural3 (Female)",
    "fr_be_female": "fr-BE-CharlineNeural (Female)",
    "fr_ca_female": "fr-CA-SylvieNeural (Female)",
    "fr_ch_female": "fr-CH-ArianeNeural (Female)",
    "fr_fr_female": "fr-FR-DeniseNeural (Female)",
    "ga_ie_female": "ga-IE-OrlaNeural3 (Female)",
    "gl_es_female": "gl-ES-SabelaNeural3 (Female)",
    "gu_in_female": "gu-IN-DhwaniNeural (Female)",
    "he_il_female": "he-IL-HilaNeural (Female)",
    "hi_in_male": "hi-IN-AaravNeural (Male)",
    "hr_hr_female": "hr-HR-GabrijelaNeural (Female)",
    "hu_hu_female": "hu-HU-NoemiNeural (Female)",
    "hy_am_female": "hy-AM-AnahitNeural3 (Female)",
    "id_id_female": "id-ID-GadisNeural (Female)",
    "is_is_female": "is-IS-GudrunNeural3 (Female)",
    "it_it_female": "it-IT-ElsaNeural (Female)",
    "iu_cans_ca_female": "iu-Cans-CA-SiqiniqNeural3 (Female)",
    "iu_latn_ca_female": "iu-Latn-CA-SiqiniqNeural3 (Female)",
    "ja_jp_female": "ja-JP-NanamiNeural (Female)",
    "jv_id_female": "jv-ID-SitiNeural3 (Female)",
    "ka_ge_female": "ka-GE-EkaNeural3 (Female)",
    "kk_kz_female": "kk-KZ-AigulNeural3 (Female)",
    "km_kh_female": "km-KH-SreymomNeural3 (Female)",
    "kn_in_female": "kn-IN-SapnaNeural3 (Female)",
    "ko_kr_female": "ko-KR-SunHiNeural (Female)",
    "lo_la_female": "lo-LA-KeomanyNeural3 (Female)",
    "lt_lt_female": "lt-LT-OnaNeural3 (Female)",
    "lv_lv_female": "lv-LV-EveritaNeural3 (Female)",
    "mk_mk_female": "mk-MK-MarijaNeural3 (Female)",
    "ml_in_female": "ml-IN-SobhanaNeural3 (Female)",
    "mn_mn_female": "mn-MN-YesuiNeural3 (Female)",
    "mr_in_female": "mr-IN-AarohiNeural (Female)",
    "ms_my_female": "ms-MY-YasminNeural (Female)",
    "mt_mt_female": "mt-MT-GraceNeural3 (Female)",
    "my_mm_female": "my-MM-NilarNeural3 (Female)",
    "nb_no_female": "nb-NO-PernilleNeural (Female)",
    "ne_np_female": "ne-NP-HemkalaNeural3 (Female)",
    "nl_be_female": "nl-BE-DenaNeural (Female)",
    "nl_nl_female": "nl-NL-FennaNeural (Female)",
    "or_in_female": "or-IN-SubhasiniNeural3 (Female)",
    "pa_in_male": "pa-IN-OjasNeural3 (Male)",
    "pl_pl_female": "pl-PL-AgnieszkaNeural (Female)",
    "ps_af_female": "ps-AF-LatifaNeural3 (Female)",
    "pt_br_female": "pt-BR-FranciscaNeural (Female)",
    "pt_pt_female": "pt-PT-RaquelNeural (Female)",
    "ro_ro_female": "ro-RO-AlinaNeural (Female)",
    "ru_ru_female": "ru-RU-SvetlanaNeural (Female)",
    "si_lk_female": "si-LK-ThiliniNeural3 (Female)",
    "sk_sk_female": "sk-SK-ViktoriaNeural (Female)",
    "sl_si_female": "sl-SI-PetraNeural (Female)",
    "so_so_female": "so-SO-UbaxNeural3 (Female)",
    "sq_al_female": "sq-AL-AnilaNeural3 (Female)",
    "sr_latn_rs_male": "sr-Latn-RS-NicholasNeural3 (Male)",
    "sr_rs_female": "sr-RS-SophieNeural3 (Female)",
    "su_id_female": "su-ID-TutiNeural3 (Female)",
    "sv_se_female": "sv-SE-SofieNeural (Female)",
    "sw_ke_female": "sw-KE-ZuriNeural3 (Female)",
    "sw_tz_female": "sw-TZ-RehemaNeural (Female)",
    "ta_in_female": "ta-IN-PallaviNeural (Female)",
    "ta_lk_female": "ta-LK-SaranyaNeural (Female)",
    "ta_my_female": "ta-MY-KaniNeural (Female)",
    "ta_sg_female": "ta-SG-VenbaNeural (Female)",
    "te_in_female": "te-IN-ShrutiNeural (Female)",
    "th_th_female": "th-TH-PremwadeeNeural (Female)",
    "tr_tr_female": "tr-TR-EmelNeural (Female)",
    "uk_ua_female": "uk-UA-PolinaNeural (Female)",
    "ur_in_female": "ur-IN-GulNeural (Female)",
    "ur_pk_female": "ur-PK-UzmaNeural (Female)",
    "uz_uz_female": "uz-UZ-MadinaNeural3 (Female)",
    "vi_vn_female": "vi-VN-HoaiMyNeural (Female)",
    "wuu_cn_female": "wuu-CN-XiaotongNeural3 (Female)",
    "yue_cn_female": "yue-CN-XiaoMinNeural3 (Female)",
    "zh_cn_female": "zh-CN-XiaoxiaoNeural (Female)",
    "zh_cn_guangxi_male": "zh-CN-guangxi-YunqiNeural1,3 (Male)",
    "zh_cn_henan_male": "zh-CN-henan-YundengNeural3 (Male)",
    "zh_cn_liaoning_female": "zh-CN-liaoning-XiaobeiNeural1,3 (Female)",
    "zh_cn_shaanxi_female": "zh-CN-shaanxi-XiaoniNeural1,3 (Female)",
    "zh_cn_shandong_male": "zh-CN-shandong-YunxiangNeural3 (Male)",
    "zh_cn_sichuan_male": "zh-CN-sichuan-YunxiNeural1,3 (Male)",
    "zh_hk_female": "zh-HK-HiuMaanNeural (Female)",
    "zh_tw_female": "zh-TW-HsiaoChenNeural (Female)",
    "zu_za_female": "zu-ZA-ThandoNeural3 (Female)",
}

# ------------------------------------
# Helpers
# ------------------------------------
async def synthesize(text: str, voice: str) -> bytes:
    if voice not in VOICES:
        raise HTTPException(status_code=400, detail="Invalid voice")

    communicate = edge_tts.Communicate(
        text=text,
        voice=VOICES[voice],
        rate="+0%",
        volume="+0%"
    )

    audio_bytes = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_bytes += chunk["data"]

    return audio_bytes

# ------------------------------------
# Routes
# ------------------------------------
@app.get("/")
def root():
    return {
        "status": "running",
        "voices": len(VOICES),
        "engine": "edge-tts"
    }

@app.get("/voices")
def list_voices():
    return VOICES

@app.get("/tts")
async def tts(
    text: str = Query(..., max_length=1000),
    voice: str = Query("en_female_1"),
    download: bool = False
):
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text is empty")

    audio = await synthesize(text, voice)

    headers = {}
    if download:
        headers["Content-Disposition"] = 'attachment; filename="speech.mp3"'

    return StreamingResponse(
        io.BytesIO(audio),
        media_type="audio/mpeg",
        headers=headers
    )

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


