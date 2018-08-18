from sqlalchemy import Column, Integer, String
from yourapplication.database import Base

class Financials(Base):
    __tablename__ = 'financials'
    ticker = Column(String, primary_key=True)
    period = Column(Date, primary_key=True)
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

    def __init__(self, ticker, period, gross_margin, operating_income, operating_margin, net_income, eps, dividends, payout_ratio, shares, bps, operating_cash_flow, cap_spending, fcf, working_capital)

        self.ticker = ticker
        self.period = period
        self.gross_margin = gross_margin
        self.operating_income = operating_income
        self.operating_margin = operating_margin
        self.net_income = net_income
        self.eps = eps
        self.dividends = dividends
        self.payout_ratio = payout_ratio
        self.shares = shares
        self.bps = bps
        self.operating_cash_flow = operating_cash_flow
        self.cap_spending = cap_spending
        self.fcf = fcf
        self.working_capital = working_capital

class Health(Base):
   __tablename__ = 'health'
   ticker = Column(String, primary_key=True)
   period = Column(String, primary_key=True)
   current_ratio = Column(Float)
   debt_equity = Column(Float)

    def __init__(self, ticker, period, current_ratio, debt_equity):
        self.ticker = ticker
        self.period = period
        self.current_ratio = current_ratio
        self.debt_equity = debt_equity



