from sqlalchemy import Column, Integer, Float, String, Date, ForeignKey
from database.database import Base


class Financial(Base):
    __tablename__ = "financials"
    ticker = Column(String(10), primary_key=True)
    dividend_yield = Column(Float)
    beta = Column(Float)
    updated = Column(Date)
    company_name = Column(String(50))

    def __repr__(self):
        return "<ticket: {ticker}, yield: {div_yield}, beta:{beta}, updated:{updated}>".format(
            ticker=self.ticker,
            div_yield=self.dividend_yield,
            beta=self.beta,
            updated=self.updated,
        )

    def dump(self):
        return dict([(k, v) for k, v in vars(self).items() if not k.startswith("_")])


class Ratio(Base):
    __tablename__ = "ratios"
    ticker = Column(String(10), ForeignKey("financials.ticker"), primary_key=True)
    period = Column(Date, primary_key=True)
    revenue = Column(Float)
    gross_margin = Column(Float)
    operating_income = Column(Float)
    operating_margin = Column(Float)
    net_income = Column(Float)
    eps = Column(Float)
    dividends = Column(Float)
    payout_ratio = Column(Float)
    shares = Column(Integer)
    bps = Column(Float)
    operating_cash_flow = Column(Float)
    cap_spending = Column(Float)
    fcf = Column(Float)
    working_capital = Column(Float)
    current_ratio = Column(Float)
    debt_equity = Column(Float)

    def __repr__(self):
        return "<ticker: {ticker}, period: {period}, eps: {eps}>".format(
            ticker=self.ticker, period=self.period, eps=self.eps
        )

    def dump(self):
        return dict([(k, v) for k, v in vars(self).items() if not k.startswith("_")])


class Valuation(Base):
    __tablename__ = "valuations"
    ticker = Column(String(10), ForeignKey("financials.ticker"), primary_key=True)
    year = Column(Date, primary_key=True)
    valuation = Column(Float)

    def __repr__(self):
        return "<ticker: {ticker}, valuation: {valuation}, year:{year}>".format(
            ticker=self.ticker, valuation=self.valuation, year=self.year
        )

    def dump(self):
        return dict([(k, v) for k, v in vars(self).items() if not k.startswith("_")])


class Dividend(Base):
    __tablename__ = "dividends"
    ticker = Column(String(10), ForeignKey("financials.ticker"), primary_key=True)
    period = Column(Date, primary_key=True)
    dividend = Column(Float)

    def __repr__(self):
        return "<ticker: {ticker}, period: {period}, dividend: {dividend}>".format(
            ticker=self.ticker, period=self.period, eps=self.dividend
        )

    def dump(self):
        return dict([(k, v) for k, v in vars(self).items() if not k.startswith("_")])
