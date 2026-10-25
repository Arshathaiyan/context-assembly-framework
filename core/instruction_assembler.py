def _val(context: dict, key: str) -> str:
    """Return the value for a key, or 'Not Specified' if empty."""
    v = context.get(key, "")
    if isinstance(v, list):
        v = ", ".join(v)
    return v.strip() if v else "Not Specified"


def build_prompt(context: dict) -> str:
    """
    Build the structured Coffee Shop AI Instruction document
    directly from the context dictionary — no API call needed.
    """
    business_name      = _val(context, "business_name")
    location           = _val(context, "location")
    objective          = _val(context, "objective")
    target_audience    = _val(context, "target_audience")
    speciality         = _val(context, "speciality")
    tone               = _val(context, "tone")
    menu_items         = _val(context, "menu_items")
    price_range        = _val(context, "price_range")
    promotion_channel  = _val(context, "promotion_channel")
    offers             = _val(context, "offers")

    final_objective = (
        f"{business_name} aims to {objective} by serving {target_audience} "
        f"in {location}. Specialising in {speciality} with a {tone} brand tone, "
        f"the shop offers {menu_items} within a {price_range} price range. "
        f"Promotions will be run through {promotion_channel} featuring {offers}."
    )

    return f"""====================================================
            COFFEE SHOP AI INSTRUCTION
====================================================

PROJECT OVERVIEW
- Business Name: {business_name}
- Business Type: Coffee Shop
- Location: {location}
- Speciality: {speciality}

BUSINESS OBJECTIVE
- Primary Objective: {objective}
- Brand Tone: {tone}

TARGET AUDIENCE
- Primary Audience: {target_audience}

MENU INFORMATION
- Menu Items: {menu_items}
- Price Range: {price_range}

PROMOTION REQUIREMENTS
- Promotion Channel: {promotion_channel}
- Offers: {offers}

IMPLEMENTATION GUIDELINES
- Use only the provided information.
- Do not add additional assumptions.
- Maintain the specified brand tone.

FINAL OBJECTIVE
{final_objective}

===================================================="""


def assemble_instruction(context: dict, template_path: str = None) -> str:
    """
    Generate the Coffee Shop AI Instruction document from context.
    No external API is used — output is built directly from user inputs.
    """
    return build_prompt(context)
